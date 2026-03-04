"""Unit tests for shared base models."""

from datetime import date, datetime

import pytest
from conftest import (
    CORRELATION_HIGH,
    INVALID_SNAPSHOT_IDS,
    METADATA_SCHEMAS,
    SAMPLE_CATALOG_ENTRY,
    VALID_SHA256_HASHES,
    VALID_SNAPSHOT_IDS,
)
from pydantic import ValidationError

from active_metadata.models import (
    CatalogEntryBase,
    ColumnRelationBase,
    MetadataBase,
    MetadataSnapshotBase,
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
            correlation=CORRELATION_HIGH,
            metadata_column=METADATA_SCHEMAS["title"],
        )
        assert r.catalog_column == "title"
        assert r.correlation == CORRELATION_HIGH
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
            ColumnRelationBase(catalog_column="title", correlation=CORRELATION_HIGH)  # type: ignore

        with pytest.raises(ValidationError):
            ColumnRelationBase(correlation=CORRELATION_HIGH, metadata_column=METADATA_SCHEMAS["title"])  # type: ignore


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
            snapshot_id=snapshot_id,  # type: ignore[arg-type]
            payload_sha256=valid_sha256,
            storage_key="test.json",
        )
        assert snapshot.snapshot_id == snapshot_id

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
    def test_invalid_snapshot_id(self, invalid_id: str, valid_sha256):
        """Test invalid snapshot_id formats are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MetadataSnapshotBase(
                snapshot_id=invalid_id,  # type: ignore[arg-type]
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
