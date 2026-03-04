"""Business logic for MetadataSnapshot."""

from typing import Optional

from active_metadata import SnapshotIdentifier
from sqlmodel import Session

from app.src.metadata_snapshot.model import MetadataSnapshot
from app.src.metadata_snapshot.repository import MetadataSnapshotRepository


class MetadataSnapshotService:
    """MetadataSnapshot service."""

    def __init__(self, repository: MetadataSnapshotRepository):
        """Initialize with repository."""
        self.repository = repository

    def save_record(
        self,
        db: Session,
        identifier: SnapshotIdentifier,
        storage_key: str,
        original_filename: Optional[str],
    ) -> MetadataSnapshot:
        """Create snapshot entity and save to DB."""
        snapshot = MetadataSnapshot(
            snapshot_id=identifier.snapshot_id,
            payload_sha256=identifier.payload_sha256,
            storage_key=storage_key,
            original_filename=original_filename,
        )
        return self.repository.save(db, snapshot)

    def get_snapshot(self, db: Session, snapshot_id: SnapshotIdentifier) -> Optional[MetadataSnapshot]:
        """Retrieve snapshot metadata by ID."""
        return self.repository.find_by_snapshot_id(db, snapshot_id)

    def find_latest_by_hash(self, db: Session, payload_sha256: str) -> Optional[MetadataSnapshot]:
        """Find most recent snapshot with matching content hash."""
        return self.repository.find_latest_by_hash(db, payload_sha256)
