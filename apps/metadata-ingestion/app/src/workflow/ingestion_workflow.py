"""Ingestion workflow orchestration."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID, uuid4

from active_metadata import SnapshotIdentifier, detect_extension
from active_metadata.models import CatalogContentFields, DraftStatus
from sqlmodel import Session

from app.config import settings
from app.src.catalog_entry.model import CatalogEntry, CatalogEntryUpdate
from app.src.catalog_entry.service import CatalogEntryService
from app.src.catalog_entry_draft.model import CatalogEntryDraft, MappingEvidence
from app.src.catalog_entry_draft.service import CatalogEntryDraftService
from app.src.catalog_merge.model import (
    CatalogMerge,
    MergeCandidate,
    MergeEvidence,
    MergeRecommendation,
)
from app.src.catalog_merge.service import CatalogMergeService
from app.src.column_relation.service import ColumnRelationService
from app.src.events import (
    DraftPhaseCompleted,
    DraftPhaseFailed,
    EventBus,
    MergePhaseCompleted,
    MergePhaseFailed,
    PublishCompleted,
    StorePhaseCompleted,
    StorePhaseFailed,
)
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
from app.src.workflow.model import DraftPhaseResult, MergePhaseResult, StorePhaseResult
from app.version import VERSION


class IngestionWorkflowService:
    """Orchestrates the ingestion workflow (Facade).

    Owns all cross-service orchestration:
    - execute_store_phase: payload → snapshot + metadata + run
    - execute_draft_phase: run → draft with mapping
    - execute_merge_phase: draft → merge (entity match + scoring + auto-approve)
    - execute_merge_approve: merge → approve + publish → catalog entry

    Domain services handle only their own state transitions.
    EventBus publishing is the facade's responsibility.
    """

    def __init__(
        self,
        snapshot_service: MetadataSnapshotService,
        metadata_entry_service: MetadataEntryService,
        ingestion_run_service: IngestionRunService,
        draft_service: CatalogEntryDraftService,
        column_relation_service: ColumnRelationService,
        file_storage: FilesystemStorage,
        event_bus: EventBus,
        catalog_merge_service: CatalogMergeService,
        catalog_entry_service: CatalogEntryService,
    ):
        """Initialize with all required services."""
        self.snapshot_service = snapshot_service
        self.metadata_entry_service = metadata_entry_service
        self.ingestion_run_service = ingestion_run_service
        self.draft_service = draft_service
        self.column_relation_service = column_relation_service
        self.file_storage = file_storage
        self.event_bus = event_bus
        self.catalog_merge_service = catalog_merge_service
        self.catalog_entry_service = catalog_entry_service

    def get_mapping_version(self) -> str:
        """Get current mapping version from app version."""
        return VERSION

    # ========================================================================
    # Store Phase
    # ========================================================================

    def execute_store_phase(
        self,
        db: Session,
        payload: str | bytes,
        filename: str | None = None,
    ) -> StorePhaseResult:
        """Store Phase: Persist metadata payload.

        1. Parse payload -> key/value pairs (fail fast)
        2. Compute payload_sha256, Generate snapshot_id
        3. Persist payload to storage (outside TX)
        4. INSERT metadata_snapshot (TX1)
        5. Bulk INSERT metadata_entry (TX1)
        6. INSERT ingestion_run (TX1, state=STORED)

        Lineage: Publishes StorePhaseCompleted/Failed events.
        """
        mapping_version = self.get_mapping_version()
        run_id = uuid4()  # Shared UUID for both ingestion_run and lineage

        try:
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

            # Step 6: Create ingestion run with shared UUID
            run = self.ingestion_run_service.create_run(
                db,
                IngestionRunCreate(
                    run_id=run_id,  # Shared UUID
                    snapshot_id=snapshot.snapshot_id,
                    mapping_version=mapping_version,
                ),
            )

            # TX1 flush
            db.flush()
            db.refresh(snapshot)
            db.refresh(run)

            # Publish COMPLETE event
            self.event_bus.publish(
                StorePhaseCompleted(
                    snapshot_id=snapshot.snapshot_id,
                    metadata_count=len(metadata_schemas),
                    original_filename=filename,
                )
            )

            return StorePhaseResult(
                snapshot_id=snapshot.snapshot_id,
                run_id=run_id,
                metadata_count=len(metadata_schemas),
            )

        except Exception as e:
            logging.error(f"Store phase failed: {e}")
            # Publish FAIL event
            self.event_bus.publish(
                StorePhaseFailed(
                    error_message=str(e),
                    original_filename=filename,
                )
            )
            raise

    # ========================================================================
    # Draft Phase
    # ========================================================================

    def execute_draft_phase(
        self,
        db: Session,
        run_id: UUID,
    ) -> DraftPhaseResult:
        """Draft Phase: Create catalog entry draft with mapping.

        1. SELECT metadata_entry for snapshot_id
        2. SELECT column_relation
        3. Build mapping (top-1 now, keep top-k evidence)
        4. INSERT catalog_entry_draft
        5. UPDATE ingestion_run.state=DRAFTED

        Lineage: Publishes DraftPhaseCompleted/Failed events.
        Parent run is Store Phase run_id (= ingestion_run.run_id).
        """
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
            db.refresh(run)

            # Publish COMPLETE event
            self.event_bus.publish(
                DraftPhaseCompleted(
                    snapshot_id=run.snapshot_id,
                    draft_id=draft.id,  # type: ignore[arg-type]
                )
            )

            return DraftPhaseResult(
                draft=draft,
                mapping_version=run.mapping_version,
            )

        except Exception as e:
            logging.error(f"Draft phase failed for run {run_id}: {e}")
            # TODO: raise 후 get_session에서 rollback되어 FAILED 상태가 저장되지 않음
            self.ingestion_run_service.mark_failed(db, run_id, str(e))
            # Publish FAIL event
            self.event_bus.publish(
                DraftPhaseFailed(
                    snapshot_id=run.snapshot_id,
                    error_message=str(e),
                )
            )
            raise

    # ========================================================================
    # Merge Phase
    # ========================================================================

    def execute_merge_phase(
        self,
        db: Session,
        draft_id: int,
        threshold: float = settings.AUTO_PUBLISH_THRESHOLD,
    ) -> MergePhaseResult:
        """Merge Phase: Entity match + scoring + auto-publish decision.

        1. Build merge evidence (candidates/recommended/score)
        2. Create merge record (CRUD)
        3. Auto-approve if score >= threshold AND candidates exist
        """
        draft = self.draft_service.get_draft(db, draft_id)
        if not draft:
            raise ValueError(f"Draft {draft_id} not found")

        try:
            # 1. Build evidence + score
            evidence, mapping_score = self._build_merge_evidence(db, draft)

            # 2. Create merge (CRUD)
            target_entry_id = evidence.recommended.entry_id if evidence.recommended else None
            merge = self.catalog_merge_service.create_merge(
                db,
                draft_id=draft.id,  # type: ignore[arg-type]
                merge_evidence=evidence.model_dump(),
                mapping_score=mapping_score,
                target_entry_id=target_entry_id,
            )

            # 3. Auto-approve if eligible
            catalog_entry = None
            if mapping_score >= threshold and evidence.candidates:
                merge, catalog_entry = self.execute_merge_approve(
                    db,
                    merge_id=merge.id,  # type: ignore[arg-type]
                    decided_by="system_auto",
                )

            return MergePhaseResult(
                merge=merge,
                auto_published=(catalog_entry is not None),
                catalog_entry_id=catalog_entry.id if catalog_entry else None,  # type: ignore[union-attr]
            )

        except Exception as e:
            logging.error(f"Merge phase failed for draft {draft_id}: {e}")
            self.event_bus.publish(
                MergePhaseFailed(
                    snapshot_id=draft.snapshot_id,
                    error_message=str(e),
                )
            )
            raise

    def execute_merge_approve(
        self,
        db: Session,
        merge_id: int,
        decided_by: str,
        target_entry_id: int | None = None,
    ) -> tuple[CatalogMerge, CatalogEntry]:
        """Approve orchestration: state change → publish → events.

        1. approve_decision (domain service — state transition only)
        2. Load draft
        3. apply_merge → CatalogEntry upsert
        4. Draft → PUBLISHED
        5. Publish lineage events
        """
        # 1. State transition
        merge = self.catalog_merge_service.approve_decision(
            db, merge_id, decided_by, target_entry_id
        )

        # 2. Load draft
        draft = self.draft_service.get_draft(db, merge.draft_id)
        if not draft:
            raise ValueError(f"Draft {merge.draft_id} not found for merge {merge_id}")

        # 3. Apply merge → CatalogEntry
        catalog_entry = self._apply_merge(db, merge, draft)

        # 4. Draft → PUBLISHED
        draft.status = DraftStatus.PUBLISHED
        db.flush()

        # 5. Lineage events
        self.event_bus.publish(
            MergePhaseCompleted(
                snapshot_id=draft.snapshot_id,
                draft_id=merge.draft_id,
                merge_id=merge.id,  # type: ignore[arg-type]
                mapping_score=merge.mapping_score,
                decided_by=decided_by,
            )
        )
        self.event_bus.publish(
            PublishCompleted(
                draft_id=merge.draft_id,
                merge_id=merge.id,  # type: ignore[arg-type]
                catalog_entry_id=catalog_entry.id,  # type: ignore[arg-type]
                recommendation_followed=self._check_recommendation_followed(merge),
                decided_by=decided_by,
            )
        )

        return merge, catalog_entry

    # ========================================================================
    # Private helpers
    # ========================================================================

    def _build_merge_evidence(
        self, db: Session, draft: CatalogEntryDraft
    ) -> tuple[MergeEvidence, float]:
        """Build merge evidence (entity match) and compute mapping score.

        Returns (evidence, mapping_score).
        """
        external_ids = draft.external_ids or []
        matching_entries = (
            self.catalog_entry_service.find_by_external_ids(db, external_ids)
            if external_ids
            else []
        )

        candidates = [
            MergeCandidate(
                entry_id=entry.id,  # type: ignore[arg-type]
                overlap_ids=[eid for eid in (entry.external_ids or []) if eid in external_ids],
                updated_at=entry.updated_at.isoformat() if entry.updated_at else None,
            )
            for entry in matching_entries
        ]
        recommended = (
            MergeRecommendation(entry_id=candidates[0].entry_id, reason="most_recent")
            if candidates
            else None
        )
        evidence = MergeEvidence(
            searched_external_ids=external_ids,
            candidates=candidates,
            recommended=recommended,
            decided=None,
        )

        mapping_score = self.compute_mapping_score(draft.mapping_evidence)

        return evidence, mapping_score

    def _apply_merge(
        self,
        db: Session,
        merge: CatalogMerge,
        draft: CatalogEntryDraft,
    ) -> CatalogEntry:
        """Apply merge: upsert CatalogEntry with full field overwrite from draft."""
        if merge.target_entry_id:
            # UPDATE existing entry: full field overwrite
            update_dto = CatalogEntryUpdate()
            for field_name in CatalogContentFields.get_content_fields():
                value = getattr(draft, field_name, None)
                if value is not None:
                    update_dto.set_field(field_name, value)
            update_dto.set_field("latest_snapshot_id", draft.snapshot_id)

            return self.catalog_entry_service.update_catalog_entry(db, merge.target_entry_id, update_dto)

        # CREATE new entry
        catalog_entry = CatalogEntry(
            title=draft.title,
            description=draft.description,
            issued=draft.issued,
            modified=draft.modified,
            publisher=draft.publisher,
            keyword=draft.keyword,
            theme=draft.theme,
            landing_page=draft.landing_page,
            access_url=draft.access_url,
            external_ids=draft.external_ids,
            latest_snapshot_id=draft.snapshot_id,
        )
        return self.catalog_entry_service.create_catalog_entry(db, catalog_entry)

    @staticmethod
    def compute_mapping_score(mapping_evidence: dict[str, Any]) -> float:
        """Compute mapping score: sum(decided.correlation) / len(content_fields).

        Pure function. Uses fixed denominator = len(CatalogContentFields.get_content_fields()).
        correlation이 None인 경우 0으로 처리.
        """
        content_field_count = len(CatalogContentFields.get_content_fields())
        if content_field_count == 0:
            return 0.0

        total_correlation = 0.0
        for _field_name, evidence_dict in mapping_evidence.items():
            try:
                evidence = MappingEvidence.model_validate(evidence_dict)
                if evidence.decided and evidence.decided.correlation is not None:
                    total_correlation += evidence.decided.correlation
            except Exception:
                continue

        return total_correlation / content_field_count

    @staticmethod
    def _check_recommendation_followed(merge: CatalogMerge) -> bool:
        """Check if the decided target matches the recommended target."""
        evidence = merge.merge_evidence
        if not isinstance(evidence, dict):
            return True
        recommended = evidence.get("recommended")
        decided = evidence.get("decided")
        if not recommended or not decided:
            return True
        return recommended.get("entry_id") == decided.get("entry_id")
