"""Database operations for CatalogMerge."""

from typing import Optional

from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import Session, select

from app.src.catalog_merge.model import CatalogMerge


class CatalogMergeRepository:
    """CatalogMerge repository."""

    def save(self, db: Session, merge: CatalogMerge) -> CatalogMerge:
        """Save merge to database."""
        db.add(merge)
        db.flush()
        return merge

    def find_by_id(self, db: Session, merge_id: int) -> Optional[CatalogMerge]:
        """Find merge by id."""
        stmt = select(CatalogMerge).where(CatalogMerge.id == merge_id)
        return db.exec(stmt).first()

    def find_by_draft_id(self, db: Session, draft_id: int) -> Optional[CatalogMerge]:
        """Find merge by draft id."""
        stmt = select(CatalogMerge).where(CatalogMerge.draft_id == draft_id)
        return db.exec(stmt).first()

    def find_all(self, db: Session, limit: int = 100, offset: int = 0) -> list[CatalogMerge]:
        """Find all merges with pagination."""
        stmt = (
            select(CatalogMerge)
            .order_by(CatalogMerge.created_at.desc())  # type: ignore
            .offset(offset)
            .limit(limit)
        )
        return list(db.exec(stmt).all())

    def update(self, db: Session, merge: CatalogMerge) -> CatalogMerge:
        """Update merge in database."""
        flag_modified(merge, "merge_evidence")
        db.add(merge)
        db.flush()
        return merge
