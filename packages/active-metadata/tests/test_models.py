"""Unit tests for shared base models."""

import time
from datetime import date, datetime

import pytest
from conftest import (
    INVALID_SNAPSHOT_IDS,
    METADATA_SCHEMAS,
    SAMPLE_CATALOG_ENTRY,
    SAMPLE_CONTENT,
    VALID_SHA256_HASHES,
    VALID_SNAPSHOT_IDS,
)
from pydantic import ValidationError

from active_metadata.models import (
    CatalogEntryBase,
    ColumnRelationBase,
    MetadataBase,
    MetadataSnapshotBase,
    SnapshotIdentifier,
)


class TestMetadataBase:
    """Tests for MetadataBase."""

    def test_creation(self, sample_metadata_entry):
        """Test MetadataBase instantiation with realistic data."""
        m = MetadataBase(**sample_metadata_entry)
        assert m.metadata_schema == METADATA_SCHEMAS["title"]
        assert m.value == SAMPLE_CATALOG_ENTRY["title"]
        assert m.metadata_id == "15107742"

    def test_nullable_value(self):
        """Test MetadataBase with None value."""
        m = MetadataBase(
            metadata_schema=METADATA_SCHEMAS["description"],
            value=None,
            metadata_id="15107742",
        )
        assert m.value is None

    def test_validation_error(self):
        """Test MetadataBase rejects invalid types."""
        with pytest.raises(ValidationError):
            MetadataBase(metadata_schema=123, value="Test", metadata_id="15107742")  # type: ignore

    def test_required_metadata_id(self):
        """Test MetadataBase requires metadata_id."""
        with pytest.raises(ValidationError):
            MetadataBase(metadata_schema=METADATA_SCHEMAS["title"], value="Test")  # type: ignore

    def test_optional_ingested_at(self):
        """Test MetadataBase with optional ingested_at."""
        m = MetadataBase(
            metadata_schema=METADATA_SCHEMAS["modified"],
            value="2024-09-25",
            metadata_id="15107742",
        )
        assert m.ingested_at is None

        now = datetime.now()
        m2 = MetadataBase(
            metadata_schema=METADATA_SCHEMAS["modified"],
            value="2024-09-25",
            metadata_id="15107742",
            ingested_at=now,
        )
        assert m2.ingested_at == now

    def test_empty_string_value(self):
        """Test MetadataBase with empty string value."""
        m = MetadataBase(
            metadata_schema=METADATA_SCHEMAS["description"],
            value="",
            metadata_id="15107742",
        )
        assert m.value == ""


class TestCatalogEntryBase:
    """Tests for CatalogEntryBase."""

    def test_minimal(self):
        """Test CatalogEntryBase with minimal required fields."""
        e = CatalogEntryBase(identifier="15107742")
        assert e.identifier == "15107742"
        assert e.title is None
        assert e.keyword is None

    def test_with_realistic_data(self, sample_catalog_entry):
        """Test CatalogEntryBase with realistic data from sample."""
        e = CatalogEntryBase(
            identifier="15107742",
            **sample_catalog_entry,
            raw_metadata={"source": "data.go.kr", "@type": "Dataset"},
        )
        assert e.identifier == "15107742"
        assert e.title == SAMPLE_CATALOG_ENTRY["title"]
        assert e.description == SAMPLE_CATALOG_ENTRY["description"]
        assert e.keyword == SAMPLE_CATALOG_ENTRY["keyword"]
        assert e.theme == SAMPLE_CATALOG_ENTRY["theme"]
        assert e.landing_page == SAMPLE_CATALOG_ENTRY["landing_page"]
        assert e.issued == date(2024, 9, 25)

    def test_default_identifier(self):
        """Test CatalogEntryBase generates UUID identifier by default."""
        e = CatalogEntryBase()
        assert e.identifier is not None
        assert len(e.identifier) > 0

    def test_default_raw_metadata(self):
        """Test CatalogEntryBase has empty dict for raw_metadata by default."""
        e = CatalogEntryBase(identifier="15107742")
        assert e.raw_metadata == {}


class TestColumnRelationBase:
    """Tests for ColumnRelationBase."""

    def test_creation(self):
        """Test ColumnRelationBase with DCAT column mapping."""
        r = ColumnRelationBase(
            catalog_column="title",
            correlation=0.95,
            metadata_column=METADATA_SCHEMAS["title"],
        )
        assert r.catalog_column == "title"
        assert r.correlation == 0.95
        assert r.metadata_column == METADATA_SCHEMAS["title"]

    @pytest.mark.parametrize(
        "correlation",
        [
            pytest.param(0.0, id="min_bound"),
            pytest.param(0.5, id="mid_value"),
            pytest.param(1.0, id="max_bound"),
        ],
    )
    def test_valid_correlation_values(self, correlation: float):
        """Test valid correlation values within bounds."""
        r = ColumnRelationBase(
            catalog_column="keyword",
            correlation=correlation,
            metadata_column=METADATA_SCHEMAS["keyword"],
        )
        assert r.correlation == correlation

    @pytest.mark.parametrize(
        "invalid_correlation",
        [
            pytest.param(-0.1, id="below_min"),
            pytest.param(1.1, id="above_max"),
            pytest.param(-1.0, id="negative"),
            pytest.param(2.0, id="way_above"),
        ],
    )
    def test_invalid_correlation_values(self, invalid_correlation: float):
        """Test invalid correlation values are rejected."""
        with pytest.raises(ValidationError):
            ColumnRelationBase(
                catalog_column="title",
                correlation=invalid_correlation,
                metadata_column=METADATA_SCHEMAS["title"],
            )

    def test_required_fields(self):
        """Test ColumnRelationBase requires all fields."""
        with pytest.raises(ValidationError):
            ColumnRelationBase(catalog_column="title", correlation=0.95)  # type: ignore

        with pytest.raises(ValidationError):
            ColumnRelationBase(correlation=0.95, metadata_column=METADATA_SCHEMAS["title"])  # type: ignore


class TestMetadataSnapshotBase:
    """Tests for MetadataSnapshotBase."""

    def test_valid_snapshot_id(self, valid_snapshot_id, valid_sha256):
        """Test valid snapshot_id format."""
        snapshot = MetadataSnapshotBase(
            snapshot_id=valid_snapshot_id,
            payload_sha256=valid_sha256,
            storage_key="2024/02/23/1708675200-a1b2c3d4e5f6.json",
        )
        assert snapshot.snapshot_id == valid_snapshot_id

    @pytest.mark.parametrize(
        "snapshot_id",
        [
            pytest.param(VALID_SNAPSHOT_IDS[0], id="wisenut_namespace"),
            pytest.param(VALID_SNAPSHOT_IDS[1], id="datagoKr_namespace"),
            pytest.param(VALID_SNAPSHOT_IDS[2], id="hyphen_namespace"),
            pytest.param(VALID_SNAPSHOT_IDS[3], id="underscore_namespace"),
        ],
    )
    def test_valid_snapshot_id_variants(self, snapshot_id: str, valid_sha256):
        """Test various valid snapshot_id formats."""
        snapshot = MetadataSnapshotBase(
            snapshot_id=snapshot_id,
            payload_sha256=valid_sha256,
            storage_key="test.json",
        )
        assert snapshot.snapshot_id == snapshot_id

    @pytest.mark.parametrize(
        "invalid_id,error_key",
        [
            pytest.param(INVALID_SNAPSHOT_IDS["missing_urn_prefix"], "missing_urn_prefix", id="missing_urn_prefix"),
            pytest.param(INVALID_SNAPSHOT_IDS["missing_dash"], "missing_dash", id="missing_dash"),
            pytest.param(INVALID_SNAPSHOT_IDS["non_numeric_timestamp"], "non_numeric_timestamp", id="non_numeric_timestamp"),
            pytest.param(INVALID_SNAPSHOT_IDS["short_hash"], "short_hash", id="short_hash"),
            pytest.param(INVALID_SNAPSHOT_IDS["non_hex_hash"], "non_hex_hash", id="non_hex_hash"),
            pytest.param(
                INVALID_SNAPSHOT_IDS["invalid_namespace_char"], "invalid_namespace_char", id="invalid_namespace_char"
            ),
            pytest.param(INVALID_SNAPSHOT_IDS["wrong_resource_type"], "wrong_resource_type", id="wrong_resource_type"),
        ],
    )
    def test_invalid_snapshot_id(self, invalid_id: str, error_key: str, valid_sha256):
        """Test invalid snapshot_id formats are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MetadataSnapshotBase(
                snapshot_id=invalid_id,
                payload_sha256=valid_sha256,
                storage_key="test.json",
            )
        assert "Invalid snapshot_id format" in str(exc_info.value)

    @pytest.mark.parametrize(
        "sha256",
        [
            pytest.param(VALID_SHA256_HASHES[0], id="all_a"),
            pytest.param(VALID_SHA256_HASHES[1], id="hex_pattern"),
            pytest.param(VALID_SHA256_HASHES[2], id="uppercase"),
        ],
    )
    def test_valid_payload_sha256(self, valid_snapshot_id, sha256: str):
        """Test valid payload_sha256 formats."""
        snapshot = MetadataSnapshotBase(
            snapshot_id=valid_snapshot_id,
            payload_sha256=sha256,
            storage_key="test.json",
        )
        assert len(snapshot.payload_sha256) == 64

    @pytest.mark.parametrize(
        "invalid_sha256",
        [
            pytest.param("abc", id="too_short"),
            pytest.param("a" * 63, id="one_char_short"),
            pytest.param("a" * 65, id="one_char_long"),
            pytest.param("g" * 64, id="non_hex_char"),
            pytest.param("GHIJ" * 16, id="invalid_uppercase"),
        ],
    )
    def test_invalid_payload_sha256(self, valid_snapshot_id, invalid_sha256: str):
        """Test invalid payload_sha256 formats are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MetadataSnapshotBase(
                snapshot_id=valid_snapshot_id,
                payload_sha256=invalid_sha256,
                storage_key="test.json",
            )
        assert "payload_sha256 must be exactly 64 hexadecimal characters" in str(exc_info.value)


class TestSnapshotIdentifier:
    """Tests for SnapshotIdentifier."""

    def test_generate_structure(self):
        """Test SnapshotIdentifier structure with realistic content."""
        identifier = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"])

        assert isinstance(identifier, SnapshotIdentifier)
        assert isinstance(identifier.snapshot_id, str)
        assert isinstance(identifier.timestamp, int)
        assert isinstance(identifier.payload_sha256, str)
        assert len(identifier.payload_sha256) == 64

    def test_generate_format(self):
        """Test snapshot_id URN format."""
        identifier = SnapshotIdentifier.generate(SAMPLE_CONTENT["xml"])

        assert identifier.snapshot_id.startswith("urn:wisenut:metadata:")

        parts = identifier.snapshot_id.split(":")
        assert len(parts) == 4
        assert parts[0] == "urn"
        assert parts[1] == "wisenut"
        assert parts[2] == "metadata"

        timestamp_hash = parts[3]
        timestamp_part, hash_part = timestamp_hash.split("-", 1)
        assert timestamp_part.isdigit()
        assert len(hash_part) == 12

    def test_generate_with_string_payload(self):
        """Test with string payload (JSON content)."""
        identifier = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"])
        assert identifier.snapshot_id.startswith("urn:wisenut:metadata:")
        assert len(identifier.payload_sha256) == 64

    def test_generate_with_bytes_payload(self):
        """Test with bytes payload (binary content)."""
        identifier = SnapshotIdentifier.generate(SAMPLE_CONTENT["binary"])
        assert identifier.snapshot_id.startswith("urn:wisenut:metadata:")
        assert len(identifier.payload_sha256) == 64

    def test_deterministic_hash(self):
        """Test that same content produces same hash (content addressable)."""
        content = SAMPLE_CONTENT["json_object"]

        id1 = SnapshotIdentifier.generate(content)
        time.sleep(1.1)
        id2 = SnapshotIdentifier.generate(content)

        # Different timestamps
        assert id1.timestamp != id2.timestamp
        assert id1.snapshot_id != id2.snapshot_id
        # Same content hash
        assert id1.payload_sha256 == id2.payload_sha256

    def test_different_content_different_hash(self):
        """Test that different content produces different hashes."""
        id1 = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"])
        id2 = SnapshotIdentifier.generate(SAMPLE_CONTENT["xml"])

        assert id1.payload_sha256 != id2.payload_sha256
        assert id1.snapshot_id != id2.snapshot_id

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
        identifier = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"], namespace=namespace)
        assert identifier.snapshot_id.startswith(expected_prefix)

    def test_storage_key_format(self):
        """Test storage_key generation format."""
        identifier = SnapshotIdentifier.generate(SAMPLE_CONTENT["json_object"])
        storage_key = identifier.generate_storage_key("json")

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
        identifier = SnapshotIdentifier(
            snapshot_id="urn:wisenut:metadata:1708675200-abcdef123456",
            timestamp=1708675200,
            payload_sha256="a" * 64,
        )
        storage_key = identifier.generate_storage_key("json")
        assert storage_key.startswith("2024/02/23/")

    @pytest.mark.parametrize("ext", ["json", "xml", "rdf", "bin", "parquet"])
    def test_storage_key_extensions(self, ext: str):
        """Test storage_key with various file extensions."""
        identifier = SnapshotIdentifier(
            snapshot_id="test",
            timestamp=int(time.time()),
            payload_sha256="a" * 64,
        )
        assert identifier.generate_storage_key(ext).endswith(f".{ext}")
