"""Lineage event service for emitting OpenLineage-compliant events."""

from datetime import datetime, timezone

from sqlmodel import Session

from active_metadata.models import LineageEventType
from app.src.lineage.builder import OpenLineageEventBuilder
from app.src.lineage.model import LineageEvent
from app.src.lineage.repository import LineageEventRepository

__all__ = ["LineageEventService"]


class LineageEventService:
    """Service for creating and storing OpenLineage events.

    Provides high-level methods for emitting events at workflow transition points.
    Events are stored in lineage_event table with full OpenLineage payload.
    """

    DB_NAMESPACE = "postgres://amm-db.wisenut.com/amm"
    FILE_NAMESPACE = "file://amm-storage"

    def __init__(self, repository: LineageEventRepository) -> None:
        """Initialize with repository."""
        self.repository = repository

    def emit_store_phase_complete(
        self,
        db: Session,
        snapshot_id: str,
        ingestion_run_id: int,
        mapping_version: str,
        storage_key: str,
        original_filename: str | None,
        payload_sha256: str,
    ) -> LineageEvent:
        """Emit COMPLETE event for Store Phase.

        Called after successful completion of Store Phase (TX1 committed).
        Records: file upload -> metadata_snapshot creation.
        """
        builder = OpenLineageEventBuilder()

        # Build input (uploaded file)
        builder.with_input_dataset(
            namespace=self.FILE_NAMESPACE,
            name=original_filename or "unknown",
        )

        # Build event payload
        payload = (
            builder.with_new_run_id()
            .with_event_type(LineageEventType.COMPLETE)
            .with_job("metadata-ingestion.store-phase")
            .with_amm_ingestion_run_facet(ingestion_run_id, mapping_version)
            .with_amm_snapshot_output_facet(snapshot_id, payload_sha256, storage_key)
            .build()
        )

        event = LineageEvent(
            event_time=datetime.now(timezone.utc),
            event_type=LineageEventType.COMPLETE,
            run_id=builder.run_id,
            job_namespace=builder.job_namespace,
            job_name=builder.job_name,
            event_payload=payload,
            snapshot_id=snapshot_id,
            ingestion_run_id=ingestion_run_id,
        )

        return self.repository.save(db, event)

    def emit_draft_phase_complete(
        self,
        db: Session,
        snapshot_id: str,
        draft_id: int,
        ingestion_run_id: int,
        mapping_version: str,
    ) -> LineageEvent:
        """Emit COMPLETE event for Draft Phase.

        Called after successful completion of Draft Phase (TX2 committed).
        Records: metadata_snapshot -> catalog_entry_draft creation.
        """
        builder = OpenLineageEventBuilder()

        # Build input (snapshot reference)
        builder.with_input_dataset(
            namespace=self.DB_NAMESPACE,
            name="metadata_snapshot",
            input_facets={
                "amm_snapshotRef": {
                    "_producer": builder.PRODUCER,
                    "_schemaURL": f"{builder.PRODUCER}/schemas/AmmSnapshotRefFacet.json",
                    "snapshotId": snapshot_id,
                }
            },
        )

        # Build event payload
        payload = (
            builder.with_new_run_id()
            .with_event_type(LineageEventType.COMPLETE)
            .with_job("metadata-ingestion.draft-phase")
            .with_amm_ingestion_run_facet(ingestion_run_id, mapping_version)
            .with_amm_draft_output_facet(draft_id, mapping_version)
            .build()
        )

        event = LineageEvent(
            event_time=datetime.now(timezone.utc),
            event_type=LineageEventType.COMPLETE,
            run_id=builder.run_id,
            job_namespace=builder.job_namespace,
            job_name=builder.job_name,
            event_payload=payload,
            snapshot_id=snapshot_id,
            draft_id=draft_id,
            ingestion_run_id=ingestion_run_id,
        )

        return self.repository.save(db, event)

    def emit_draft_phase_failed(
        self,
        db: Session,
        snapshot_id: str,
        ingestion_run_id: int,
        mapping_version: str,
        error_message: str,
    ) -> LineageEvent:
        """Emit FAIL event for Draft Phase.

        Called when Draft Phase fails with exception.
        """
        builder = OpenLineageEventBuilder()

        # Build input (snapshot reference)
        builder.with_input_dataset(
            namespace=self.DB_NAMESPACE,
            name="metadata_snapshot",
            input_facets={
                "amm_snapshotRef": {
                    "_producer": builder.PRODUCER,
                    "_schemaURL": f"{builder.PRODUCER}/schemas/AmmSnapshotRefFacet.json",
                    "snapshotId": snapshot_id,
                }
            },
        )

        # Build event payload with error facet
        payload = (
            builder.with_new_run_id()
            .with_event_type(LineageEventType.FAIL)
            .with_job("metadata-ingestion.draft-phase")
            .with_amm_ingestion_run_facet(ingestion_run_id, mapping_version)
            .with_run_facet(
                "errorMessage",
                {
                    "_producer": builder.PRODUCER,
                    "_schemaURL": "https://openlineage.io/spec/facets/1-0-1/ErrorMessageRunFacet.json",
                    "message": error_message,
                    "programmingLanguage": "Python",
                },
            )
            .build()
        )

        event = LineageEvent(
            event_time=datetime.now(timezone.utc),
            event_type=LineageEventType.FAIL,
            run_id=builder.run_id,
            job_namespace=builder.job_namespace,
            job_name=builder.job_name,
            event_payload=payload,
            snapshot_id=snapshot_id,
            ingestion_run_id=ingestion_run_id,
        )

        return self.repository.save(db, event)

    def emit_publish_complete(
        self,
        db: Session,
        draft_id: int,
        catalog_entry_id: int,
        identifier: str,
        snapshot_id: str,
    ) -> LineageEvent:
        """Emit COMPLETE event for Draft Publish.

        Called after draft is successfully published to catalog_entry.
        """
        builder = OpenLineageEventBuilder()

        # Build input (draft reference)
        builder.with_input_dataset(
            namespace=self.DB_NAMESPACE,
            name="catalog_entry_draft",
            input_facets={
                "amm_draftRef": {
                    "_producer": builder.PRODUCER,
                    "_schemaURL": f"{builder.PRODUCER}/schemas/AmmDraftRefFacet.json",
                    "draftId": draft_id,
                }
            },
        )

        # Build event payload
        payload = (
            builder.with_new_run_id()
            .with_event_type(LineageEventType.COMPLETE)
            .with_job("catalog-service.publish")
            .with_amm_catalog_entry_output_facet(catalog_entry_id, identifier)
            .build()
        )

        event = LineageEvent(
            event_time=datetime.now(timezone.utc),
            event_type=LineageEventType.COMPLETE,
            run_id=builder.run_id,
            job_namespace=builder.job_namespace,
            job_name=builder.job_name,
            event_payload=payload,
            snapshot_id=snapshot_id,
            draft_id=draft_id,
            catalog_entry_id=catalog_entry_id,
        )

        return self.repository.save(db, event)

    def emit_discard_complete(
        self,
        db: Session,
        draft_id: int,
        snapshot_id: str,
    ) -> LineageEvent:
        """Emit COMPLETE event for Draft Discard.

        Called after draft is discarded (status -> DISCARDED).
        """
        builder = OpenLineageEventBuilder()

        # Build input (draft reference)
        builder.with_input_dataset(
            namespace=self.DB_NAMESPACE,
            name="catalog_entry_draft",
            input_facets={
                "amm_draftRef": {
                    "_producer": builder.PRODUCER,
                    "_schemaURL": f"{builder.PRODUCER}/schemas/AmmDraftRefFacet.json",
                    "draftId": draft_id,
                }
            },
        )

        # Build event payload (no output - just status change)
        payload = (
            builder.with_new_run_id()
            .with_event_type(LineageEventType.COMPLETE)
            .with_job("catalog-service.discard")
            .build()
        )

        event = LineageEvent(
            event_time=datetime.now(timezone.utc),
            event_type=LineageEventType.COMPLETE,
            run_id=builder.run_id,
            job_namespace=builder.job_namespace,
            job_name=builder.job_name,
            event_payload=payload,
            snapshot_id=snapshot_id,
            draft_id=draft_id,
        )

        return self.repository.save(db, event)

    def find_events(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        job_name: str | None = None,
        event_type: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[LineageEvent]:
        """Find lineage events with optional filters."""
        return self.repository.find_all(
            db,
            limit=limit,
            offset=offset,
            job_name=job_name,
            event_type=event_type,
            snapshot_id=snapshot_id,
        )
