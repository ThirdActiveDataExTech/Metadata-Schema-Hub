"""Ingestion workflow orchestration (Store Phase + Draft Phase)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from active_metadata import SnapshotIdentifier, detect_extension
from sqlmodel import Session

from app.src.catalog_entry_draft.service import CatalogEntryDraftService
from app.src.column_relation.service import ColumnRelationService
from app.src.file_converter.file_handler import MetadataFile, process_metadata_file
from app.src.ingestion_run.exceptions import (
    IngestionRunNotFoundError,
    InvalidIngestionRunStateError,
    NoMetadataEntriesError,
)
from app.src.ingestion_run.model import IngestionRunCreate
from app.src.ingestion_run.service import IngestionRunService
from app.src.metadata_entry.model import MetadataCreate
from app.src.metadata_entry.service import MetadataEntryService
from app.src.metadata_snapshot.filesystem_storage import FilesystemStorage
from app.src.metadata_snapshot.service import MetadataSnapshotService
from app.src.workflow.model import DraftPhaseResult, StorePhaseResult
from app.version import VERSION

if TYPE_CHECKING:
    from app.src.lineage.service import LineageEventService


class IngestionWorkflowService:
    """Orchestrates the two-phase ingestion workflow (Facade)."""

    def __init__(
        self,
        snapshot_service: MetadataSnapshotService,
        metadata_entry_service: MetadataEntryService,
        ingestion_run_service: IngestionRunService,
        draft_service: CatalogEntryDraftService,
        column_relation_service: ColumnRelationService,
        file_storage: FilesystemStorage,
        lineage_service: Optional[LineageEventService] = None,
    ):
        """Initialize with all required services."""
        self.snapshot_service = snapshot_service
        self.metadata_entry_service = metadata_entry_service
        self.ingestion_run_service = ingestion_run_service
        self.draft_service = draft_service
        self.column_relation_service = column_relation_service
        self.file_storage = file_storage
        self.lineage_service = lineage_service

    def get_mapping_version(self) -> str:
        """Get current mapping version from app version."""
        return VERSION

    def execute_store_phase(
        self,
        db: Session,
        payload: str | bytes,
        filename: Optional[str] = None,
    ) -> StorePhaseResult:
        """Store Phase: Persist metadata payload.

        1. Parse payload -> key/value pairs (fail fast)
        2. Compute payload_sha256, Generate snapshot_id
        3. Persist payload to storage (outside TX)
        4. INSERT metadata_snapshot (TX1)
        5. Bulk INSERT metadata_entry (TX1)
        6. INSERT ingestion_run (TX1, state=STORED)
        """
        mapping_version = self.get_mapping_version()

        # Step 1: Parse payload first (fail fast, nothing saved yet)
        metadata_file = MetadataFile(filename=filename, content=payload)
        _, metadata_schemas = process_metadata_file(metadata_file)

        # Step 2-3: Generate identifier and save file (outside TX)
        identifier = SnapshotIdentifier.generate(payload)
        extension = detect_extension(payload, filename)
        storage_key = identifier.generate_storage_key(extension)
        self.file_storage.save(storage_key, payload)

        # Step 4: Create snapshot DB record (TX1)
        snapshot = self.snapshot_service.save_record(
            db, identifier=identifier, storage_key=storage_key, original_filename=filename
        )

        # Step 5: Bulk insert metadata entries (metadata_id = snapshot_id)
        metadata_create = MetadataCreate(
            metadata_id=snapshot.snapshot_id,
            metadata_schemas=metadata_schemas,
        )
        self.metadata_entry_service.create(db, metadata_create)

        # Step 7: Create ingestion run
        run = self.ingestion_run_service.create_run(
            db,
            IngestionRunCreate(snapshot_id=snapshot.snapshot_id, mapping_version=mapping_version),
        )

        # TX1 flush
        db.flush()
        db.refresh(snapshot)
        db.refresh(run)

        # Emit lineage event
        if self.lineage_service:
            self.lineage_service.emit_store_phase_complete(
                db,
                snapshot_id=snapshot.snapshot_id,
                ingestion_run_id=run.run_id,  # type: ignore[arg-type]
                mapping_version=mapping_version,
                storage_key=storage_key,
                original_filename=filename,
                payload_sha256=identifier.payload_sha256 or snapshot.payload_sha256,
            )
            db.flush()

        return StorePhaseResult(
            snapshot_id=snapshot.snapshot_id,
            run_id=run.run_id,  # type: ignore[arg-type]
            metadata_count=len(metadata_schemas),
        )

    def execute_draft_phase(
        self,
        db: Session,
        run_id: int,
    ) -> DraftPhaseResult:
        """Draft Phase: Create catalog entry draft with mapping.

        1. SELECT metadata_entry for snapshot_id
        2. SELECT column_relation
        3. Build mapping (top-1 now, keep top-k evidence)
        4. INSERT catalog_entry_draft
        5. UPDATE ingestion_run.state=DRAFTED
        """
        # Get the run
        run = self.ingestion_run_service.get_run(db, run_id)
        if not run:
            raise IngestionRunNotFoundError(run_id)

        if run.state.value != "STORED":
            raise InvalidIngestionRunStateError(run_id, str(run.state))

        try:
            # Step 1: Get metadata entries (metadata_id = snapshot_id)
            metadata_entries = self.metadata_entry_service.select_metadata(db, run.snapshot_id)

            if not metadata_entries:
                raise NoMetadataEntriesError(run.snapshot_id)

            # Step 2: Get column relations for matching schemas
            metadata_schemas = list(set(e.metadata_schema for e in metadata_entries))
            relations = self.column_relation_service.get_relations_by_metadata_columns(db, metadata_schemas)

            # Step 3-4: Create draft with mapping
            draft = self.draft_service.create_draft(
                db,
                snapshot_id=run.snapshot_id,
                mapping_version=run.mapping_version,
                metadata_entries=metadata_entries,
                relations=relations,
            )

            # Step 5: Update run state
            self.ingestion_run_service.mark_drafted(db, run_id, draft.id)  # type: ignore[arg-type]

            # TX2 flush
            db.flush()
            db.refresh(draft)

            # Emit lineage event
            if self.lineage_service:
                self.lineage_service.emit_draft_phase_complete(
                    db,
                    snapshot_id=run.snapshot_id,
                    draft_id=draft.id,  # type: ignore[arg-type]
                    ingestion_run_id=run_id,
                    mapping_version=run.mapping_version,
                )
                db.flush()
                db.refresh(draft)

            return DraftPhaseResult(
                draft=draft,
                run_id=run_id,
                mapping_version=run.mapping_version,
            )

        except Exception as e:
            logging.error(f"Draft phase failed for run {run_id}: {e}")
            self.ingestion_run_service.mark_failed(db, run_id, str(e))
            # Emit failure event
            if self.lineage_service:
                self.lineage_service.emit_draft_phase_failed(
                    db,
                    snapshot_id=run.snapshot_id,
                    ingestion_run_id=run_id,
                    mapping_version=run.mapping_version,
                    error_message=str(e),
                )
                db.flush()
            raise
