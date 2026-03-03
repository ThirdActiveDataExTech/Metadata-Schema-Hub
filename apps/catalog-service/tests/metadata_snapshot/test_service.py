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

    def test_passes_snapshot_id_to_repository(
        self,
        metadata_snapshot_service: MetadataSnapshotService,
        mock_metadata_snapshot_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should pass snapshot_id directly to repository."""
        mock_metadata_snapshot_repository.find_by_snapshot_id.return_value = None
        snapshot_id = SnapshotIdentifier("urn:wisenut:metadata:1234567890-abcdef123456")

        metadata_snapshot_service.get_snapshot(mock_db, snapshot_id)

        mock_metadata_snapshot_repository.find_by_snapshot_id.assert_called_once_with(mock_db, snapshot_id)
