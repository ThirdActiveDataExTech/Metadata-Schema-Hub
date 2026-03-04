"""Tests for MetadataSnapshotService."""

from unittest.mock import MagicMock

from active_metadata.types import SnapshotIdentifier
from app.src.metadata_snapshot.model import MetadataSnapshot
from app.src.metadata_snapshot.service import MetadataSnapshotService


class TestGetSnapshot:
    """Tests for get_snapshot method."""

    def test_returns_snapshot_by_id(
        self,
        metadata_snapshot_service: MetadataSnapshotService,
        mock_metadata_snapshot_repository: MagicMock,
        mock_db: MagicMock,
        sample_metadata_snapshot: MetadataSnapshot,
    ) -> None:
        """Should return snapshot when found by ID."""
        mock_metadata_snapshot_repository.find_by_snapshot_id.return_value = sample_metadata_snapshot
        snapshot_id = SnapshotIdentifier("urn:wisenut:metadata:1705312800-abc123def456")

        result = metadata_snapshot_service.get_snapshot(mock_db, snapshot_id)

        assert result == sample_metadata_snapshot
        mock_metadata_snapshot_repository.find_by_snapshot_id.assert_called_once_with(mock_db, snapshot_id)

    def test_returns_none_when_not_found(
        self,
        metadata_snapshot_service: MetadataSnapshotService,
        mock_metadata_snapshot_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return None when snapshot not found."""
        mock_metadata_snapshot_repository.find_by_snapshot_id.return_value = None
        snapshot_id = SnapshotIdentifier("urn:wisenut:metadata:1705312800-000000000000")

        result = metadata_snapshot_service.get_snapshot(mock_db, snapshot_id)

        assert result is None
        mock_metadata_snapshot_repository.find_by_snapshot_id.assert_called_once_with(mock_db, snapshot_id)


class TestLoadRawContent:
    """Tests for load_raw_content method."""

    def test_returns_bytes_from_storage(
        self,
        metadata_snapshot_service: MetadataSnapshotService,
        mock_metadata_snapshot_repository: MagicMock,
        mock_filesystem_storage: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return raw bytes from storage."""
        mock_snapshot = MagicMock()
        mock_snapshot.storage_key = "2024/01/01/test.json"
        mock_snapshot_content = b'{"title": "Test"}'
        
        mock_metadata_snapshot_repository.find_by_snapshot_id.return_value = mock_snapshot
        mock_filesystem_storage.load.return_value = mock_snapshot_content

        result = metadata_snapshot_service.load_raw_content(
            mock_db, "urn:wisenut:metadata:1705312800-abc123def456"
        )

        assert result == mock_snapshot_content
        mock_filesystem_storage.load.assert_called_once_with(mock_snapshot.storage_key)

    def test_returns_none_when_snapshot_not_found(
        self,
        metadata_snapshot_service: MetadataSnapshotService,
        mock_metadata_snapshot_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return None when snapshot not found."""
        mock_metadata_snapshot_repository.find_by_snapshot_id.return_value = None

        result = metadata_snapshot_service.load_raw_content(
            mock_db, "urn:wisenut:metadata:1705312800-000000000000"
        )

        assert result is None

    def test_returns_none_when_file_not_found(
        self,
        metadata_snapshot_service: MetadataSnapshotService,
        mock_metadata_snapshot_repository: MagicMock,
        mock_filesystem_storage: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return None when file not found in storage."""
        mock_snapshot = MagicMock()
        mock_snapshot.storage_key = "2024/01/01/missing.json"
        mock_metadata_snapshot_repository.find_by_snapshot_id.return_value = mock_snapshot
        mock_filesystem_storage.load.side_effect = FileNotFoundError()

        result = metadata_snapshot_service.load_raw_content(
            mock_db, "urn:wisenut:metadata:1705312800-abc123def456"
        )

        assert result is None
