"""Unit tests for custom types."""

from datetime import UTC, datetime

import pytest
from conftest import (
    INVALID_SNAPSHOT_IDS,
    SAMPLE_CONTENT,
    VALID_SNAPSHOT_IDS,
)
from pydantic import BaseModel, ValidationError

from active_metadata.types import SnapshotIdentifier


class TestSnapshotIdentifierValidation:
    """Tests for SnapshotIdentifier validation."""

    @pytest.mark.parametrize(
        "snapshot_id",
        [
            pytest.param(VALID_SNAPSHOT_IDS[0], id="wisenut_namespace"),
            pytest.param(VALID_SNAPSHOT_IDS[1], id="datagoKr_namespace"),
            pytest.param(VALID_SNAPSHOT_IDS[2], id="hyphen_namespace"),
            pytest.param(VALID_SNAPSHOT_IDS[3], id="underscore_namespace"),
        ],
    )
    def test_valid_snapshot_ids(self, snapshot_id: str):
        """Test valid snapshot_id formats."""
        sid = SnapshotIdentifier(snapshot_id)
        assert str(sid) == snapshot_id
        assert isinstance(sid, str)
        assert isinstance(sid, SnapshotIdentifier)

    @pytest.mark.parametrize(
        "invalid_id",
        [
            pytest.param(INVALID_SNAPSHOT_IDS["missing_urn_prefix"], id="missing_urn_prefix"),
            pytest.param(INVALID_SNAPSHOT_IDS["missing_dash"], id="missing_dash"),
            pytest.param(INVALID_SNAPSHOT_IDS["non_numeric_timestamp"], id="non_numeric_timestamp"),
            pytest.param(INVALID_SNAPSHOT_IDS["short_hash"], id="short_hash"),
            pytest.param(INVALID_SNAPSHOT_IDS["non_hex_hash"], id="non_hex_hash"),
            pytest.param(INVALID_SNAPSHOT_IDS["invalid_namespace_char"], id="invalid_namespace_char"),
            pytest.param(INVALID_SNAPSHOT_IDS["wrong_resource_type"], id="wrong_resource_type"),
        ],
    )
    def test_invalid_snapshot_ids(self, invalid_id: str):
        """Test invalid snapshot_id formats are rejected."""
        with pytest.raises(ValueError, match="Invalid snapshot_id format"):
            SnapshotIdentifier(invalid_id)


class TestSnapshotIdentifierGenerate:
    """Tests for SnapshotIdentifier.generate()."""

    def test_generate_structure(self):
        """Test SnapshotIdentifier.generate() returns valid SnapshotIdentifier."""
        sid = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"])
        assert isinstance(sid, SnapshotIdentifier)
        assert sid.startswith("urn:wisenut:metadata:")

    def test_generate_format(self):
        """Test snapshot_id URN format."""
        sid = SnapshotIdentifier.generate(SAMPLE_CONTENT["xml"])

        parts = str(sid).split(":")
        assert len(parts) == 4
        assert parts[0] == "urn"
        assert parts[1] == "wisenut"
        assert parts[2] == "metadata"

        timestamp_hash = parts[3]
        timestamp_part, hash_part = timestamp_hash.split("-", 1)
        assert timestamp_part.isdigit()
        assert len(hash_part) == 12

    def test_generate_with_string_payload(self):
        """Test with string payload."""
        sid = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"])
        assert sid.startswith("urn:wisenut:metadata:")
        assert sid.payload_sha256 is not None
        assert len(sid.payload_sha256) == SnapshotIdentifier.SHA256_HEX_LENGTH

    def test_generate_with_bytes_payload(self):
        """Test with bytes payload."""
        sid = SnapshotIdentifier.generate(SAMPLE_CONTENT["binary"])
        assert sid.startswith("urn:wisenut:metadata:")
        assert sid.payload_sha256 is not None
        assert len(sid.payload_sha256) == SnapshotIdentifier.SHA256_HEX_LENGTH

    def test_payload_sha256_from_string(self):
        """Test payload_sha256 is None when created from string."""
        sid = SnapshotIdentifier("urn:wisenut:metadata:1708675200-abcdef123456")
        assert sid.payload_sha256 is None

    def test_payload_sha256_matches_hash_prefix(self):
        """Test payload_sha256 starts with hash_prefix."""
        sid = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"])
        assert sid.payload_sha256 is not None
        assert sid.payload_sha256.startswith(sid.hash_prefix)

    def test_generate_with_custom_timestamp(self):
        """Test generate with explicit timestamp."""
        ts = 1708675200  # 2024-02-23 08:00:00 UTC
        sid = SnapshotIdentifier.generate("test", timestamp=ts)
        assert sid.timestamp == ts

    def test_deterministic_hash(self):
        """Test that same content produces same hash (content addressable)."""
        content = SAMPLE_CONTENT["json_object"]

        sid1 = SnapshotIdentifier.generate(content, timestamp=1000000000)
        sid2 = SnapshotIdentifier.generate(content, timestamp=2000000000)

        # Different timestamps = different IDs
        assert sid1.timestamp != sid2.timestamp
        assert sid1 != sid2
        # Same content = same hash prefix
        assert sid1.hash_prefix == sid2.hash_prefix

    def test_different_content_different_hash(self):
        """Test that different content produces different hashes."""
        sid1 = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"])
        sid2 = SnapshotIdentifier.generate(SAMPLE_CONTENT["xml"])

        assert sid1.hash_prefix != sid2.hash_prefix
        assert sid1 != sid2

    @pytest.mark.parametrize(
        "namespace,expected_prefix",
        [
            pytest.param("wisenut", "urn:wisenut:metadata:", id="default"),
            pytest.param("datagoKr", "urn:datagoKr:metadata:", id="camelCase"),
            pytest.param("data-go-kr", "urn:data-go-kr:metadata:", id="with_hyphen"),
            pytest.param("data_go_kr", "urn:data_go_kr:metadata:", id="with_underscore"),
        ],
    )
    def test_namespace_variants(self, namespace: str, expected_prefix: str):
        """Test various namespace formats."""
        sid = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"], namespace=namespace)
        assert sid.startswith(expected_prefix)


class TestSnapshotIdentifierProperties:
    """Tests for SnapshotIdentifier property accessors."""

    @pytest.fixture
    def sample_snapshot_id(self) -> SnapshotIdentifier:
        """Fixed snapshot_id for property tests."""
        return SnapshotIdentifier("urn:wisenut:metadata:1708675200-abcdef123456")

    def test_namespace(self, sample_snapshot_id):
        """Test namespace extraction."""
        assert sample_snapshot_id.namespace == "wisenut"

    def test_timestamp(self, sample_snapshot_id):
        """Test timestamp extraction."""
        assert sample_snapshot_id.timestamp == 1708675200

    def test_hash_prefix(self, sample_snapshot_id):
        """Test hash_prefix extraction."""
        assert sample_snapshot_id.hash_prefix == "abcdef123456"

    def test_datetime_utc(self, sample_snapshot_id):
        """Test datetime_utc conversion."""
        dt = sample_snapshot_id.datetime_utc
        assert dt == datetime(2024, 2, 23, 8, 0, 0, tzinfo=UTC)

    def test_properties_cached(self, sample_snapshot_id):
        """Test that _parsed is cached (same object)."""
        _ = sample_snapshot_id.namespace
        _ = sample_snapshot_id.timestamp
        _ = sample_snapshot_id.hash_prefix
        # _parsed should be cached after first access
        assert hasattr(sample_snapshot_id, "_parsed")

    @pytest.mark.parametrize(
        "snapshot_id,expected_ns",
        [
            ("urn:wisenut:metadata:1000-aaaaaaaaaaaa", "wisenut"),
            ("urn:datagoKr:metadata:1000-aaaaaaaaaaaa", "datagoKr"),
            ("urn:my-org:metadata:1000-aaaaaaaaaaaa", "my-org"),
            ("urn:my_org:metadata:1000-aaaaaaaaaaaa", "my_org"),
        ],
    )
    def test_namespace_variants(self, snapshot_id: str, expected_ns: str):
        """Test namespace extraction from various formats."""
        sid = SnapshotIdentifier(snapshot_id)
        assert sid.namespace == expected_ns


class TestSnapshotIdentifierStorageKey:
    """Tests for SnapshotIdentifier.generate_storage_key()."""

    def test_storage_key_format(self):
        """Test storage_key generation format."""
        sid = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"])
        storage_key = sid.generate_storage_key("json")

        parts = storage_key.split("/")
        assert len(parts) == 4

        year, month, day, filename = parts
        assert len(year) == 4 and year.isdigit()
        assert len(month) == 2 and month.isdigit()
        assert len(day) == 2 and day.isdigit()
        assert filename.endswith(".json")

    def test_storage_key_utc(self):
        """Test that storage_key uses UTC timezone."""
        # 2024-02-23 08:00:00 UTC
        sid = SnapshotIdentifier("urn:wisenut:metadata:1708675200-abcdef123456")
        storage_key = sid.generate_storage_key("json")
        assert storage_key.startswith("2024/02/23/")
        assert storage_key == "2024/02/23/1708675200-abcdef123456.json"

    @pytest.mark.parametrize("ext", ["json", "xml", "rdf", "bin", "parquet"])
    def test_storage_key_extensions(self, ext: str):
        """Test storage_key with various file extensions."""
        sid = SnapshotIdentifier("urn:wisenut:metadata:1708675200-abcdef123456")
        assert sid.generate_storage_key(ext).endswith(f".{ext}")


class TestSnapshotIdentifierPydanticIntegration:
    """Tests for Pydantic integration."""

    def test_pydantic_model_validation(self):
        """Test SnapshotIdentifier works in Pydantic model."""

        class TestModel(BaseModel):
            snapshot_id: SnapshotIdentifier

        model = TestModel(snapshot_id="urn:wisenut:metadata:1708675200-abcdef123456")
        assert isinstance(model.snapshot_id, SnapshotIdentifier)
        assert model.snapshot_id.namespace == "wisenut"

    def test_pydantic_model_invalid(self):
        """Test Pydantic rejects invalid snapshot_id."""

        class TestModel(BaseModel):
            snapshot_id: SnapshotIdentifier

        with pytest.raises(ValidationError):
            TestModel(snapshot_id="invalid-id")

    def test_pydantic_serialization(self):
        """Test SnapshotIdentifier serializes to string."""

        class TestModel(BaseModel):
            snapshot_id: SnapshotIdentifier

        model = TestModel(snapshot_id="urn:wisenut:metadata:1708675200-abcdef123456")
        data = model.model_dump()
        assert data["snapshot_id"] == "urn:wisenut:metadata:1708675200-abcdef123456"

    def test_pydantic_json_serialization(self):
        """Test SnapshotIdentifier serializes to JSON string."""

        class TestModel(BaseModel):
            snapshot_id: SnapshotIdentifier

        model = TestModel(snapshot_id="urn:wisenut:metadata:1708675200-abcdef123456")
        json_str = model.model_dump_json()
        assert '"urn:wisenut:metadata:1708675200-abcdef123456"' in json_str

    def test_pydantic_json_schema(self):
        """Test SnapshotIdentifier generates correct JSON schema."""

        class TestModel(BaseModel):
            snapshot_id: SnapshotIdentifier

        schema = TestModel.model_json_schema()
        props = schema["properties"]["snapshot_id"]
        assert props["type"] == "string"
        assert "pattern" in props
        assert "urn:" in props["pattern"]
