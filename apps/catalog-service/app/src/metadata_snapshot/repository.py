"""Read-only repository for MetadataSnapshot."""

from typing import Optional

from sqlmodel import Session, select

from app.src.metadata_snapshot.model import MetadataSnapshot


class MetadataSnapshotRepository:
    """MetadataSnapshot repository (read-only)."""

    def find_by_snapshot_id(self, db: Session, snapshot_id: str) -> Optional[MetadataSnapshot]:
        """Find snapshot by snapshot_id."""
        stmt = select(MetadataSnapshot).where(MetadataSnapshot.snapshot_id == snapshot_id)
        return db.exec(stmt).first()
