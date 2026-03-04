"""Read-only filesystem storage for metadata snapshots."""

from pathlib import Path


class FilesystemStorage:
    """Read-only local filesystem storage for snapshot files."""

    def __init__(self, base_path: str = "./snapshots"):
        """Initialize with base storage path."""
        self.base_path = Path(base_path)

    def load(self, storage_key: str) -> bytes:
        """Load content from storage_key."""
        return (self.base_path / storage_key).read_bytes()

    def exists(self, storage_key: str) -> bool:
        """Check if storage_key exists."""
        return (self.base_path / storage_key).exists()
