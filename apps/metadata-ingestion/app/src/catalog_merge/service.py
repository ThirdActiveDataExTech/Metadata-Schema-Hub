"""CatalogMerge domain service (CRUD + state transitions)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from active_metadata.models import MergeDecision
from sqlmodel import Session

from app.src.catalog_merge.exceptions import MergeNotFoundError, MergeNotPendingError
from app.src.catalog_merge.model import (
    CatalogMerge,
    MergeDecided,
    MergeEvidence,
)
from app.src.catalog_merge.repository import CatalogMergeRepository


class CatalogMergeService:
    """CatalogMerge domain service.

    Thin service: CRUD + state transitions (approve_decision/reject).
    No external service dependencies. No orchestration.
    All cross-service logic (apply_merge, events, draft status) belongs in the workflow facade.
    """

    def __init__(self, repository: CatalogMergeRepository):
        """Initialize with repository only."""
        self.repository = repository

    def create_merge(
        self,
        db: Session,
        *,
        draft_id: int,
        merge_evidence: dict[str, Any],
        mapping_score: float,
        target_entry_id: int | None = None,
    ) -> CatalogMerge:
        """Create merge record as PENDING. Pure CRUD — no orchestration logic.

        All data (evidence, score, target) must be pre-computed by the caller.
        """
        merge = CatalogMerge(
            draft_id=draft_id,
            target_entry_id=target_entry_id,
            merge_evidence=merge_evidence,
            mapping_score=mapping_score,
            decision=MergeDecision.PENDING,
        )
        return self.repository.save(db, merge)

    def approve_decision(
        self,
        db: Session,
        merge_id: int,
        decided_by: str,
        target_entry_id: int | None = None,
    ) -> CatalogMerge:
        """PENDING → APPROVED state transition only.

        No publish, no events, no external service calls.
        Returns updated merge.
        """
        merge = self.repository.find_by_id(db, merge_id)
        if not merge:
            raise MergeNotFoundError(merge_id)

        if merge.decision != MergeDecision.PENDING:
            raise MergeNotPendingError(merge_id, merge.decision)

        merge.decision = MergeDecision.APPROVED
        merge.decided_by = decided_by
        merge.decided_at = datetime.now(timezone.utc)

        if target_entry_id is not None:
            merge.target_entry_id = target_entry_id
            evidence = MergeEvidence.model_validate(merge.merge_evidence)
            evidence.decided = MergeDecided(entry_id=target_entry_id, decided_by=decided_by)
            merge.merge_evidence = evidence.model_dump()

        return self.repository.update(db, merge)

    def reject(self, db: Session, merge_id: int, decided_by: str) -> CatalogMerge:
        """PENDING → REJECTED state transition."""
        merge = self.repository.find_by_id(db, merge_id)
        if not merge:
            raise MergeNotFoundError(merge_id)

        if merge.decision != MergeDecision.PENDING:
            raise MergeNotPendingError(merge_id, merge.decision)

        merge.decision = MergeDecision.REJECTED
        merge.decided_by = decided_by
        merge.decided_at = datetime.now(timezone.utc)
        return self.repository.update(db, merge)

    def get_merge(self, db: Session, merge_id: int) -> CatalogMerge | None:
        """Get merge by ID."""
        return self.repository.find_by_id(db, merge_id)

    def get_merge_by_draft(self, db: Session, draft_id: int) -> CatalogMerge | None:
        """Get merge by draft ID."""
        return self.repository.find_by_draft_id(db, draft_id)

    def get_all_merges(self, db: Session, limit: int = 100, offset: int = 0) -> list[CatalogMerge]:
        """Get all merges with pagination."""
        return self.repository.find_all(db, limit, offset)
