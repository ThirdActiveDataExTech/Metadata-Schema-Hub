"""Lineage event service for catalog-service (read-only)."""

from typing import Any
from uuid import UUID

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

    def get_events_by_run(self, db: Session, run_id: UUID) -> list[LineageEvent]:
        """Get all events for a specific run."""
        return self.repository.find_by_run_id(db, run_id)

    def get_events_by_snapshot(
        self, db: Session, snapshot_id: str, limit: int = 100, offset: int = 0
    ) -> list[LineageEvent]:
        """Get events by snapshot ID."""
        return self.repository.find_by_snapshot_id(db, snapshot_id, limit, offset)

    def get_events_by_catalog_entry(
        self, db: Session, catalog_entry_id: int
    ) -> list[LineageEvent]:
        """Get events by catalog entry ID."""
        return self.repository.find_by_catalog_entry_id(db, catalog_entry_id)

    def list_events(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        job_name: str | None = None,
        event_type: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[LineageEvent]:
        """List events with optional filters."""
        return self.repository.find_all(
            db,
            limit=limit,
            offset=offset,
            job_name=job_name,
            event_type=event_type,
            snapshot_id=snapshot_id,
        )

    def count_events(
        self,
        db: Session,
        job_name: str | None = None,
        event_type: str | None = None,
        snapshot_id: str | None = None,
    ) -> int:
        """Count events with optional filters."""
        return self.repository.count(
            db,
            job_name=job_name,
            event_type=event_type,
            snapshot_id=snapshot_id,
        )

    def get_lineage_graph(
        self, db: Session, snapshot_id: str
    ) -> dict[str, Any]:
        """Get lineage graph for a snapshot.

        Returns upstream lineage: all events that led to the current state.
        """
        events = self.repository.find_by_snapshot_id(db, snapshot_id, limit=100)

        # Build graph structure
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        for event in events:
            # Extract inputs/outputs from payload
            payload = event.event_payload or {}
            inputs = payload.get("inputs", [])
            outputs = payload.get("outputs", [])

            # Extract filename from inputs
            filename = None
            if inputs and len(inputs) > 0:
                filename = inputs[0].get("name")

            # Add event as node with additional info
            node: dict[str, Any] = {
                "id": str(event.run_id),
                "type": "run",
                "job": event.job_name,
                "eventType": event.event_type,
                "eventTime": event.event_time.isoformat(),
                "draftId": event.draft_id,
                "catalogEntryId": event.catalog_entry_id,
                "filename": filename,
            }
            nodes.append(node)

            for inp in inputs:
                edge = {
                    "source": f"{inp.get('namespace')}/{inp.get('name')}",
                    "target": str(event.run_id),
                    "type": "input",
                }
                edges.append(edge)

            for out in outputs:
                edge = {
                    "source": str(event.run_id),
                    "target": f"{out.get('namespace')}/{out.get('name')}",
                    "type": "output",
                }
                edges.append(edge)

        return {
            "snapshotId": snapshot_id,
            "nodes": nodes,
            "edges": edges,
            "eventCount": len(events),
        }
