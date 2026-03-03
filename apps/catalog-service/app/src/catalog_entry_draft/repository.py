"""Read-only repository for CatalogEntryDraft."""

from typing import Optional

from sqlmodel import Session, select

from app.src.catalog_entry_draft.model import CatalogEntryDraft


class CatalogEntryDraftRepository:
    """CatalogEntryDraft repository (read-only)."""

    def find_by_id(self, db: Session, draft_id: int) -> Optional[CatalogEntryDraft]:
        """Find draft by id."""
        stmt = select(CatalogEntryDraft).where(CatalogEntryDraft.id == draft_id)
        return db.exec(stmt).first()

    def find_by_snapshot_id(self, db: Session, snapshot_id: str, limit: int = 100, offset: int = 0) -> list[CatalogEntryDraft]:
        """Find all drafts for a snapshot."""
        stmt = (
            select(CatalogEntryDraft)
            .where(CatalogEntryDraft.snapshot_id == snapshot_id)
            .order_by(CatalogEntryDraft.created_at.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )
        return list(db.exec(stmt).all())

    def find_all(self, db: Session, limit: int = 100, offset: int = 0) -> list[CatalogEntryDraft]:
        """Find all drafts with pagination."""
        stmt = (
            select(CatalogEntryDraft)
            .order_by(CatalogEntryDraft.created_at.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )
        return list(db.exec(stmt).all())
