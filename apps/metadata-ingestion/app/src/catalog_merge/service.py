"""Business logic for CatalogMerge (entity match + field merge, single service)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from active_metadata.models import CatalogContentFields, DraftStatus, MergeDecision
from sqlmodel import Session

from app.config import settings
from app.src.catalog_entry.model import CatalogEntry, CatalogEntryUpdate
from app.src.catalog_entry.service import CatalogEntryService
from app.src.catalog_entry_draft.model import CatalogEntryDraft, MappingEvidence
from app.src.catalog_entry_draft.service import CatalogEntryDraftService
from app.src.catalog_merge.exceptions import MergeNotFoundError, MergeNotPendingError
from app.src.catalog_merge.model import (
    CatalogMerge,
    MergeCandidate,
    MergeDecided,
    MergeEvidence,
    MergeRecommendation,
)
from app.src.catalog_merge.repository import CatalogMergeRepository
from app.src.events import EventBus, MergePhaseCompleted, PublishCompleted


class CatalogMergeService:
    """Combined match + merge service.

    Workflow:
    1. Extract external_ids from draft
    2. Find matching catalog entries (entity match)
    3. Build merge_evidence (3-key pattern)
    4. Compute mapping_score from draft's mapping_evidence
    5. Auto-approve if score >= threshold AND candidates exist
    6. Save CatalogMerge record
    """

    def __init__(
        self,
        repository: CatalogMergeRepository,
        catalog_entry_service: CatalogEntryService,
        event_bus: EventBus,
    ):
        """Initialize with repository, catalog entry service, and event bus."""
        self.repository = repository
        self.catalog_entry_service = catalog_entry_service
        self.event_bus = event_bus

    def create_merge(
        self,
        db: Session,
        draft: CatalogEntryDraft,
        threshold: float | None = None,
    ) -> CatalogMerge:
        """Create merge record: entity match + scoring + auto-approve decision."""
        if threshold is None:
            threshold = settings.AUTO_PUBLISH_THRESHOLD

        # Step 1: Extract external_ids from draft
        external_ids = draft.external_ids or []

        # Step 2: Find matching catalog entries
        matching_entries = self.catalog_entry_service.find_by_external_ids(db, external_ids) if external_ids else []

        # Step 3: Build merge_evidence
        candidates = [
            MergeCandidate(
                entry_id=entry.id,  # type: ignore[arg-type]
                overlap_ids=[eid for eid in (entry.external_ids or []) if eid in external_ids],
                updated_at=entry.updated_at.isoformat() if entry.updated_at else None,
            )
            for entry in matching_entries
        ]

        recommended = MergeRecommendation(entry_id=candidates[0].entry_id, reason="most_recent") if candidates else None

        # Step 4: Compute mapping_score
        mapping_score = self.compute_mapping_score(draft.mapping_evidence)

        # Step 5: Auto-approve decision
        decided: MergeDecided | None = None
        decision = MergeDecision.PENDING
        decided_by: str | None = None
        decided_at: datetime | None = None

        if mapping_score >= threshold and candidates:
            decided = MergeDecided(
                entry_id=recommended.entry_id,  # type: ignore[union-attr]
                decided_by="system_auto",
            )
            decision = MergeDecision.APPROVED
            decided_by = "system_auto"
            decided_at = datetime.now(timezone.utc)

        merge_evidence = MergeEvidence(
            searched_external_ids=external_ids,
            candidates=candidates,
            recommended=recommended,
            decided=decided,
        )

        target_entry_id = decided.entry_id if decided else (recommended.entry_id if recommended else None)

        # Step 6: Save
        merge = CatalogMerge(
            draft_id=draft.id,  # type: ignore[arg-type]
            target_entry_id=target_entry_id,
            merge_evidence=merge_evidence.model_dump(),
            mapping_score=mapping_score,
            decision=decision,
            decided_at=decided_at,
            decided_by=decided_by,
        )
        return self.repository.save(db, merge)

    @staticmethod
    def compute_mapping_score(mapping_evidence: dict[str, Any]) -> float:
        """Compute mapping score: sum(decided.correlation) / len(content_fields).

        Pure function for testability.
        Uses fixed denominator = len(CatalogContentFields.get_content_fields()).
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

    def approve(
        self,
        db: Session,
        merge_id: int,
        decided_by: str,
        draft_service: CatalogEntryDraftService,
        target_entry_id: int | None = None,
    ) -> tuple[CatalogMerge, CatalogEntry]:
        """Approve merge + publish: approve → apply_merge → CatalogEntry upsert.

        Single action: approve = 승인 + 발행.
        Returns (merge, catalog_entry).
        """
        merge = self.repository.find_by_id(db, merge_id)
        if not merge:
            raise MergeNotFoundError(merge_id)

        if merge.decision != MergeDecision.PENDING:
            raise MergeNotPendingError(merge_id, merge.decision)

        # 1. Update merge decision
        merge.decision = MergeDecision.APPROVED
        merge.decided_by = decided_by
        merge.decided_at = datetime.now(timezone.utc)

        if target_entry_id is not None:
            merge.target_entry_id = target_entry_id
            evidence = MergeEvidence.model_validate(merge.merge_evidence)
            evidence.decided = MergeDecided(entry_id=target_entry_id, decided_by=decided_by)
            merge.merge_evidence = evidence.model_dump()

        self.repository.update(db, merge)

        # 2. Load draft + apply merge → CatalogEntry
        draft = draft_service.get_draft(db, merge.draft_id)
        if not draft:
            raise MergeNotFoundError(merge_id)

        catalog_entry = self.apply_merge(db, merge, draft)

        # 3. Draft → PUBLISHED
        draft.status = DraftStatus.PUBLISHED
        db.flush()

        # 4. Lineage events
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
                recommendation_followed=True,
                decided_by=decided_by,
            )
        )

        return merge, catalog_entry

    def reject(self, db: Session, merge_id: int, decided_by: str) -> CatalogMerge:
        """Reject a merge."""
        merge = self.repository.find_by_id(db, merge_id)
        if not merge:
            raise MergeNotFoundError(merge_id)

        if merge.decision != MergeDecision.PENDING:
            raise MergeNotPendingError(merge_id, merge.decision)

        merge.decision = MergeDecision.REJECTED
        merge.decided_by = decided_by
        merge.decided_at = datetime.now(timezone.utc)
        return self.repository.update(db, merge)

    def apply_merge(
        self,
        db: Session,
        merge: CatalogMerge,
        draft: CatalogEntryDraft,
    ) -> CatalogEntry:
        """Apply merge: upsert CatalogEntry with full field overwrite from draft.

        No field_decisions. All content fields from draft overwrite the target.
        """
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

    def get_merge(self, db: Session, merge_id: int) -> CatalogMerge | None:
        """Get merge by ID."""
        return self.repository.find_by_id(db, merge_id)

    def get_merge_by_draft(self, db: Session, draft_id: int) -> CatalogMerge | None:
        """Get merge by draft ID."""
        return self.repository.find_by_draft_id(db, draft_id)

    def get_all_merges(self, db: Session, limit: int = 100, offset: int = 0) -> list[CatalogMerge]:
        """Get all merges with pagination."""
        return self.repository.find_all(db, limit, offset)
