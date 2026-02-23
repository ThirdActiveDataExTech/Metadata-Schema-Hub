"""Unit tests for model validation."""

import pytest
from pydantic import ValidationError

from active_metadata.models import MetadataSnapshotBase


def test_metadata_snapshot_valid_snapshot_id():
    """Test valid snapshot_id format."""
    valid_snapshot = MetadataSnapshotBase(
        snapshot_id="urn:wisenut:metadata:1708675200-a1b2c3d4e5f6",
        payload_sha256="a" * 64,
        storage_key="2024/02/23/1708675200-a1b2c3d4e5f6.json",
    )
    assert valid_snapshot.snapshot_id == "urn:wisenut:metadata:1708675200-a1b2c3d4e5f6"


def test_metadata_snapshot_invalid_snapshot_id_prefix():
    """Test snapshot_id with invalid prefix."""
    with pytest.raises(ValidationError) as exc_info:
        MetadataSnapshotBase(
            snapshot_id="invalid:prefix:1708675200-a1b2c3d4e5f6",
            payload_sha256="a" * 64,
            storage_key="test.json",
        )
    assert "snapshot_id must start with" in str(exc_info.value)


def test_metadata_snapshot_invalid_snapshot_id_no_dash():
    """Test snapshot_id without dash separator."""
    with pytest.raises(ValidationError) as exc_info:
        MetadataSnapshotBase(
            snapshot_id="urn:wisenut:metadata:1708675200a1b2c3d4e5f6",
            payload_sha256="a" * 64,
            storage_key="test.json",
        )
    assert "timestamp-hash format" in str(exc_info.value)


def test_metadata_snapshot_invalid_timestamp_non_numeric():
    """Test snapshot_id with non-numeric timestamp."""
    with pytest.raises(ValidationError) as exc_info:
        MetadataSnapshotBase(
            snapshot_id="urn:wisenut:metadata:abc-a1b2c3d4e5f6",
            payload_sha256="a" * 64,
            storage_key="test.json",
        )
    assert "Timestamp part must be numeric" in str(exc_info.value)


def test_metadata_snapshot_invalid_hash_length():
    """Test snapshot_id with incorrect hash length."""
    with pytest.raises(ValidationError) as exc_info:
        MetadataSnapshotBase(
            snapshot_id="urn:wisenut:metadata:1708675200-abc",  # Only 3 chars
            payload_sha256="a" * 64,
            storage_key="test.json",
        )
    assert "Hash part must be exactly 12 characters" in str(exc_info.value)


def test_metadata_snapshot_invalid_hash_non_hex():
    """Test snapshot_id with non-hexadecimal hash."""
    with pytest.raises(ValidationError) as exc_info:
        MetadataSnapshotBase(
            snapshot_id="urn:wisenut:metadata:1708675200-ghijklmnopqr",
            payload_sha256="a" * 64,
            storage_key="test.json",
        )
    assert "Hash part must be hexadecimal" in str(exc_info.value)


def test_metadata_snapshot_valid_payload_sha256():
    """Test valid payload_sha256 format."""
    valid_snapshot = MetadataSnapshotBase(
        snapshot_id="urn:wisenut:metadata:1708675200-a1b2c3d4e5f6",
        payload_sha256="abcdef1234567890" * 4,  # 64 hex chars
        storage_key="test.json",
    )
    assert len(valid_snapshot.payload_sha256) == 64


def test_metadata_snapshot_invalid_payload_sha256_length():
    """Test payload_sha256 with incorrect length."""
    with pytest.raises(ValidationError) as exc_info:
        MetadataSnapshotBase(
            snapshot_id="urn:wisenut:metadata:1708675200-a1b2c3d4e5f6",
            payload_sha256="abc",  # Too short
            storage_key="test.json",
        )
    assert "payload_sha256 must be exactly 64 characters" in str(exc_info.value)


def test_metadata_snapshot_invalid_payload_sha256_non_hex():
    """Test payload_sha256 with non-hexadecimal characters."""
    with pytest.raises(ValidationError) as exc_info:
        MetadataSnapshotBase(
            snapshot_id="urn:wisenut:metadata:1708675200-a1b2c3d4e5f6",
            payload_sha256="g" * 64,  # 'g' is not hex
            storage_key="test.json",
        )
    assert "payload_sha256 must be hexadecimal" in str(exc_info.value)


def test_metadata_snapshot_case_insensitive_hex():
    """Test that hex validation is case-insensitive."""
    valid_snapshot = MetadataSnapshotBase(
        snapshot_id="urn:wisenut:metadata:1708675200-ABCDEF123456",  # Uppercase
        payload_sha256="ABCDEF1234567890" * 4,  # Uppercase
        storage_key="test.json",
    )
    assert valid_snapshot.snapshot_id == "urn:wisenut:metadata:1708675200-ABCDEF123456"
    assert valid_snapshot.payload_sha256 == "ABCDEF1234567890" * 4


def test_metadata_snapshot_custom_namespace():
    """Test custom namespace in snapshot_id."""
    valid_snapshot = MetadataSnapshotBase(
        snapshot_id="urn:myorg:metadata:1708675200-a1b2c3d4e5f6",
        payload_sha256="a" * 64,
        storage_key="test.json",
    )
    assert valid_snapshot.snapshot_id == "urn:myorg:metadata:1708675200-a1b2c3d4e5f6"


def test_metadata_snapshot_namespace_with_hyphens():
    """Test namespace with hyphens is valid."""
    valid_snapshot = MetadataSnapshotBase(
        snapshot_id="urn:my-org:metadata:1708675200-a1b2c3d4e5f6",
        payload_sha256="a" * 64,
        storage_key="test.json",
    )
    assert valid_snapshot.snapshot_id == "urn:my-org:metadata:1708675200-a1b2c3d4e5f6"


def test_metadata_snapshot_namespace_with_underscores():
    """Test namespace with underscores is valid."""
    valid_snapshot = MetadataSnapshotBase(
        snapshot_id="urn:my_org:metadata:1708675200-a1b2c3d4e5f6",
        payload_sha256="a" * 64,
        storage_key="test.json",
    )
    assert valid_snapshot.snapshot_id == "urn:my_org:metadata:1708675200-a1b2c3d4e5f6"


def test_metadata_snapshot_invalid_namespace_special_chars():
    """Test namespace with invalid special characters."""
    with pytest.raises(ValidationError) as exc_info:
        MetadataSnapshotBase(
            snapshot_id="urn:my@org:metadata:1708675200-a1b2c3d4e5f6",
            payload_sha256="a" * 64,
            storage_key="test.json",
        )
    assert "Namespace must be alphanumeric" in str(exc_info.value)


def test_metadata_snapshot_invalid_resource_type():
    """Test snapshot_id with wrong resource type."""
    with pytest.raises(ValidationError) as exc_info:
        MetadataSnapshotBase(
            snapshot_id="urn:wisenut:data:1708675200-a1b2c3d4e5f6",
            payload_sha256="a" * 64,
            storage_key="test.json",
        )
    assert "Resource type must be 'metadata'" in str(exc_info.value)
