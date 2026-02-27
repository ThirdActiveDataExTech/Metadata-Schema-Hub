"""Read-only service for CatalogEntryDraft."""

from typing import Any, Optional

from sqlmodel import Session

from app.src.catalog_entry_draft.model import CatalogEntryDraft
from app.src.catalog_entry_draft.repository import CatalogEntryDraftRepository


class CatalogEntryDraftService:
    """CatalogEntryDraft service (read-only)."""

    def __init__(self, repository: CatalogEntryDraftRepository):
        """Initialize with repository."""
        self.repository = repository

    def get_draft(self, db: Session, draft_id: int) -> Optional[CatalogEntryDraft]:
        """Get draft by ID."""
        return self.repository.find_by_id(db, draft_id)

    def get_drafts_by_snapshot(self, db: Session, snapshot_id: str) -> list[CatalogEntryDraft]:
        """Get all drafts for a snapshot."""
        return self.repository.find_by_snapshot_id(db, snapshot_id)

    def get_all_drafts(self, db: Session, limit: int = 100, offset: int = 0) -> list[CatalogEntryDraft]:
        """Get all drafts with pagination."""
        return self.repository.find_all(db, limit, offset)

    def get_mapping_evidence(self, db: Session, draft_id: int) -> Optional[dict[str, Any]]:
        """Get mapping evidence for a draft."""
        draft = self.get_draft(db, draft_id)
        if draft:
            return draft.mapping_evidence
        return None
