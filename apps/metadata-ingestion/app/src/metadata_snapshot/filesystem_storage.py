"""Filesystem storage for metadata snapshots."""

from pathlib import Path


class FilesystemStorage:
    """Local filesystem storage for snapshot files."""

    def __init__(self, base_path: str = "./snapshots"):
        """Initialize with base storage path."""
        self.base_path = Path(base_path)

    def save(self, storage_key: str, payload: str | bytes) -> None:
        """Save payload to storage_key path."""
        path = self.base_path / storage_key
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_bytes(payload)

    def load(self, storage_key: str) -> bytes:
        """Load content from storage_key."""
        path = self.base_path / storage_key
        return path.read_bytes()

    def exists(self, storage_key: str) -> bool:
        """Check if storage_key exists."""
        return (self.base_path / storage_key).exists()
