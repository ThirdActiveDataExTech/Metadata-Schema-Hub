"""Read-only service for MetadataSnapshot."""

from typing import Optional

from active_metadata.types import SnapshotIdentifier
from sqlmodel import Session

from app.src.metadata_snapshot.filesystem_storage import FilesystemStorage
from app.src.metadata_snapshot.model import MetadataSnapshot
from app.src.metadata_snapshot.repository import MetadataSnapshotRepository


class MetadataSnapshotService:
    """MetadataSnapshot service (read-only operations)."""

    def __init__(self, repository: MetadataSnapshotRepository, storage: FilesystemStorage):
        """Initialize with repository and storage backend."""
        self.repository = repository
        self.storage = storage

    def get_snapshot(self, db: Session, snapshot_id: SnapshotIdentifier) -> Optional[MetadataSnapshot]:
        """Retrieve snapshot metadata by ID."""
        return self.repository.find_by_snapshot_id(db, snapshot_id)

    def load_raw_content(self, db: Session, snapshot_id: str) -> bytes | None:
        """Load raw content from storage.

        Args:
            db: Database session
            snapshot_id: Snapshot identifier string

        Returns:
            Raw bytes or None if not found
        """
        snapshot = self.repository.find_by_snapshot_id(db, snapshot_id)
        if not snapshot:
            return None

        try:
            return self.storage.load(snapshot.storage_key)
        except FileNotFoundError:
            return None
