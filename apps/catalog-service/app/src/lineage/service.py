"""Lineage event service for catalog-service (read-only)."""

from typing import Any

from active_metadata.types import EntityURI
from sqlmodel import Session

from app.src.lineage.model import LineageEvent
from app.src.lineage.repository import LineageEventRepository

__all__ = ["LineageEventService"]


class LineageEventService:
    """Service for querying lineage events (read-only)."""

    def __init__(self, repository: LineageEventRepository) -> None:
        """Initialize with repository."""
        self.repository = repository

    def get_event(self, db: Session, event_id: int) -> LineageEvent | None:
        """Get single event by ID."""
        return self.repository.find_by_id(db, event_id)

    def get_events_by_snapshot(self, db: Session, snapshot_id: str, limit: int = 100, offset: int = 0) -> list[LineageEvent]:
        """Get events by snapshot ID."""
        ref = EntityURI.snapshot(snapshot_id)
        return self.repository.find_by_ref(db, ref, limit, offset)

    def get_events_by_catalog_entry(self, db: Session, catalog_entry_id: int) -> list[LineageEvent]:
        """Get events by catalog entry ID."""
        ref = EntityURI.catalog(catalog_entry_id)
        return self.repository.find_by_ref(db, ref)

    def list_events(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        job_name: str | None = None,
        event_type: str | None = None,
    ) -> list[LineageEvent]:
        """List events with optional filters."""
        return self.repository.find_all(
            db,
            limit=limit,
            offset=offset,
            job_name=job_name,
            event_type=event_type,
        )

    def count_events(
        self,
        db: Session,
        job_name: str | None = None,
        event_type: str | None = None,
    ) -> int:
        """Count events with optional filters."""
        return self.repository.count(
            db,
            job_name=job_name,
            event_type=event_type,
        )

    def get_lineage_graph(self, db: Session, snapshot_id: str) -> dict[str, Any]:
        """Get lineage graph for a snapshot.

        Returns graph with job nodes and edges (input/output connections).
        """
        ref = EntityURI.snapshot(snapshot_id)
        events = self.repository.find_downstream(db, ref)
        return self._build_graph(snapshot_id, events, key="snapshotId")

    def get_full_downstream(self, db: Session, snapshot_id: str) -> dict[str, Any]:
        """Get full lineage chain downstream from a snapshot.

        Traces: snapshot → draft → catalog_entry
        """
        ref = EntityURI.snapshot(snapshot_id)
        events = self.repository.find_downstream(db, ref)
        return self._build_graph(snapshot_id, events, key="entityId")

    def get_full_upstream(self, db: Session, catalog_entry_id: int) -> dict[str, Any]:
        """Get full lineage chain upstream to a catalog entry.

        Traces: catalog_entry → draft → snapshot → file (reverse)
        """
        ref = EntityURI.catalog(catalog_entry_id)
        events = self.repository.find_upstream(db, ref)
        return self._build_graph(str(catalog_entry_id), events, key="entityId")

    def _build_graph(self, entity_id: str, events: list[LineageEvent], key: str = "entityId") -> dict[str, Any]:
        """Build graph response from events.

        Uses model's to_graph_node() for job nodes.
        """
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        seen_nodes: set[str] = set()

        for event in events:
            # Add job node using model method
            node = event.to_graph_node()
            job_node_id = node["id"]

            if job_node_id not in seen_nodes:
                nodes.append(node)
                seen_nodes.add(job_node_id)

            # Add input dataset nodes and edges
            for input_ref in event.input_refs or []:
                if input_ref not in seen_nodes:
                    _, table, eid = EntityURI.parse(input_ref)
                    nodes.append({"id": input_ref, "type": "dataset", "name": f"{table}/{eid}"})
                    seen_nodes.add(input_ref)
                edges.append({"source": input_ref, "target": job_node_id, "type": "input"})

            # Add output dataset nodes and edges
            for output_ref in event.output_refs or []:
                if output_ref not in seen_nodes:
                    _, table, eid = EntityURI.parse(output_ref)
                    nodes.append({"id": output_ref, "type": "dataset", "name": f"{table}/{eid}"})
                    seen_nodes.add(output_ref)
                edges.append({"source": job_node_id, "target": output_ref, "type": "output"})

        return {
            key: entity_id,
            "nodes": nodes,
            "edges": edges,
            "eventCount": len(events),
        }
