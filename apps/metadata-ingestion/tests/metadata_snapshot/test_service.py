"""Tests for MetadataSnapshotService."""

from unittest.mock import MagicMock

import pytest

from active_metadata import SnapshotIdentifier
from app.src.metadata_snapshot.model import MetadataSnapshot


class TestMetadataSnapshotService:
    """Test cases for MetadataSnapshotService."""

    @pytest.fixture
    def snapshot_identifier(self, valid_sha256):
        """Create a mock SnapshotIdentifier."""
        identifier = MagicMock(spec=SnapshotIdentifier)
        identifier.snapshot_id = "urn:wisenut:metadata:1708675200-a1b2c3d4"
        identifier.payload_sha256 = valid_sha256
        return identifier

    # ========================================================================
    # save_record tests
    # ========================================================================

    def test_save_record_creates_snapshot(self, metadata_snapshot_service, mock_db_session, snapshot_identifier):
        """Should create MetadataSnapshot entity and save."""
        metadata_snapshot_service.repository.save.side_effect = lambda db, s: s

        result = metadata_snapshot_service.save_record(
            mock_db_session,
            identifier=snapshot_identifier,
            storage_key="2024/01/test.json",
            original_filename="test.json",
        )

        assert isinstance(result, MetadataSnapshot)
        assert result.snapshot_id == snapshot_identifier.snapshot_id
        assert result.payload_sha256 == snapshot_identifier.payload_sha256
        assert result.storage_key == "2024/01/test.json"
        assert result.original_filename == "test.json"

    def test_save_record_with_none_filename(self, metadata_snapshot_service, mock_db_session, snapshot_identifier):
        """Should handle None original_filename."""
        metadata_snapshot_service.repository.save.side_effect = lambda db, s: s

        result = metadata_snapshot_service.save_record(
            mock_db_session,
            identifier=snapshot_identifier,
            storage_key="2024/01/unknown.dat",
            original_filename=None,
        )

        assert result.original_filename is None

    def test_save_record_calls_repository(self, metadata_snapshot_service, mock_db_session, snapshot_identifier):
        """Should call repository.save."""
        metadata_snapshot_service.save_record(
            mock_db_session,
            identifier=snapshot_identifier,
            storage_key="key",
            original_filename="file.json",
        )

        metadata_snapshot_service.repository.save.assert_called_once()

    # ========================================================================
    # get_snapshot tests
    # ========================================================================

    def test_get_snapshot_found(self, metadata_snapshot_service, mock_db_session, snapshot_identifier):
        """Should return snapshot when found."""
        expected = MagicMock(spec=MetadataSnapshot)
        metadata_snapshot_service.repository.find_by_snapshot_id.return_value = expected

        result = metadata_snapshot_service.get_snapshot(mock_db_session, snapshot_identifier)

        assert result == expected
        metadata_snapshot_service.repository.find_by_snapshot_id.assert_called_once_with(
            mock_db_session, snapshot_identifier
        )

    def test_get_snapshot_not_found(self, metadata_snapshot_service, mock_db_session, snapshot_identifier):
        """Should return None when not found."""
        metadata_snapshot_service.repository.find_by_snapshot_id.return_value = None

        result = metadata_snapshot_service.get_snapshot(mock_db_session, snapshot_identifier)

        assert result is None

    # ========================================================================
    # find_latest_by_hash tests
    # ========================================================================

    def test_find_latest_by_hash_found(self, metadata_snapshot_service, mock_db_session, valid_sha256):
        """Should return latest snapshot with matching hash."""
        expected = MagicMock(spec=MetadataSnapshot)
        metadata_snapshot_service.repository.find_latest_by_hash.return_value = expected

        result = metadata_snapshot_service.find_latest_by_hash(mock_db_session, valid_sha256)

        assert result == expected
        metadata_snapshot_service.repository.find_latest_by_hash.assert_called_once_with(mock_db_session, valid_sha256)

    def test_find_latest_by_hash_not_found(self, metadata_snapshot_service, mock_db_session, valid_sha256):
        """Should return None when no matching hash."""
        metadata_snapshot_service.repository.find_latest_by_hash.return_value = None

        result = metadata_snapshot_service.find_latest_by_hash(mock_db_session, valid_sha256)

        assert result is None


class TestMetadataSnapshotHashValidation:
    """Test hash validation at model level.

    Note: SQLModel does not run Pydantic field validators by default.
    Validation only runs with model_validate() or at DB save time.
    These tests document current behavior.
    """

    def test_model_accepts_any_hash_without_explicit_validation(self):
        """Document: SQLModel allows invalid hash at model creation.

        The field_validator on payload_sha256 only runs with model_validate().
        """
        from active_metadata import SnapshotIdentifier

        snapshot_id = SnapshotIdentifier("urn:wisenut:metadata:1708675200-a1b2c3d4e5f6")

        # This should ideally fail but SQLModel doesn't validate by default
        snapshot = MetadataSnapshot(
            snapshot_id=snapshot_id,
            payload_sha256="invalid_short_hash",
            storage_key="test/key.json",
        )

        # Documents current behavior: no validation at model creation
        assert snapshot.payload_sha256 == "invalid_short_hash"

    def test_valid_hash_accepted(self, valid_sha256):
        """Should accept valid 64-character hex hash."""
        from active_metadata import SnapshotIdentifier

        snapshot_id = SnapshotIdentifier("urn:wisenut:metadata:1708675200-a1b2c3d4e5f6")

        snapshot = MetadataSnapshot(
            snapshot_id=snapshot_id,
            payload_sha256=valid_sha256,
            storage_key="test/key.json",
        )

        assert snapshot.payload_sha256 == valid_sha256
