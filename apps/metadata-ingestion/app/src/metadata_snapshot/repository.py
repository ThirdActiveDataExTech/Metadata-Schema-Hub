"""Database operations for MetadataSnapshot."""

from typing import Optional

from sqlmodel import Session, select

from app.src.metadata_snapshot.model import MetadataSnapshot


class MetadataSnapshotRepository:
    """MetadataSnapshot repository."""

    def save(self, db: Session, snapshot: MetadataSnapshot) -> MetadataSnapshot:
        """Save snapshot to database."""
        db.add(snapshot)
        db.flush()
        return snapshot

    def find_by_snapshot_id(self, db: Session, snapshot_id: str) -> Optional[MetadataSnapshot]:
        """Find snapshot by snapshot_id."""
        stmt = select(MetadataSnapshot).where(MetadataSnapshot.snapshot_id == snapshot_id)
        return db.exec(stmt).first()

    def find_latest_by_hash(self, db: Session, payload_sha256: str) -> Optional[MetadataSnapshot]:
        """Find most recent snapshot with matching content hash."""
        # TODO: ingested_at만으로는 동일 시간 삽입 시 순서 보장 안됨. id로 secondary ordering 추가 필요
        stmt = (
            select(MetadataSnapshot)
            .where(MetadataSnapshot.payload_sha256 == payload_sha256)
            .order_by(MetadataSnapshot.ingested_at.desc())  # type: ignore[union-attr]
            .limit(1)
        )
        return db.exec(stmt).first()
