"""Unit tests for shared base models."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from active_metadata.models import (
    CatalogEntryBase,
    ColumnRelationBase,
    MetadataBase,
)


def test_metadata_base_creation():
    """Test MetadataBase instantiation."""
    m = MetadataBase(metadata_schema="dc.title", value="Test Title", metadata_id="test-uuid")
    assert m.metadata_schema == "dc.title"
    assert m.value == "Test Title"
    assert m.metadata_id == "test-uuid"


def test_metadata_base_nullable_value():
    """Test MetadataBase with None value."""
    m = MetadataBase(metadata_schema="dc.title", value=None, metadata_id="test-uuid")
    assert m.metadata_schema == "dc.title"
    assert m.value is None


def test_metadata_base_validation_error():
    """Test MetadataBase rejects invalid types."""
    with pytest.raises(ValidationError):
        MetadataBase(metadata_schema=123, value="Test", metadata_id="test-uuid")  # type: ignore


def test_metadata_base_required_metadata_id():
    """Test MetadataBase requires metadata_id."""
    with pytest.raises(ValidationError):
        MetadataBase(metadata_schema="dc.title", value="Test")  # type: ignore - missing metadata_id


def test_metadata_base_optional_ingested_at():
    """Test MetadataBase with optional ingested_at."""
    m = MetadataBase(metadata_schema="dc.title", value="Test", metadata_id="test-uuid")
    assert m.ingested_at is None

    now = datetime.now()
    m_with_timestamp = MetadataBase(metadata_schema="dc.title", value="Test", metadata_id="test-uuid", ingested_at=now)
    assert m_with_timestamp.ingested_at == now


def test_metadata_base_empty_string():
    """Test MetadataBase with empty string value."""
    m = MetadataBase(metadata_schema="dc.title", value="", metadata_id="test-uuid")
    assert m.value == ""


def test_catalog_entry_base_minimal():
    """Test CatalogEntryBase with minimal required fields."""
    e = CatalogEntryBase(identifier="test-id")
    assert e.identifier == "test-id"
    assert e.title is None
    assert e.keyword is None


def test_catalog_entry_base_with_all_fields():
    """Test CatalogEntryBase with all fields populated."""
    e = CatalogEntryBase(
        identifier="test-id",
        title="Test Dataset",
        description="Test Description",
        issued=date(2024, 1, 1),
        modified=date(2024, 1, 15),
        publisher="Test Publisher",
        keyword=["data", "science"],
        landing_page="https://example.com",
        theme=["education", "research"],
        access_url="https://data.example.com",
        raw_metadata={"source": "test"},
    )
    assert e.identifier == "test-id"
    assert e.title == "Test Dataset"
    assert e.description == "Test Description"
    assert e.issued == date(2024, 1, 1)
    assert e.modified == date(2024, 1, 15)
    assert e.publisher == "Test Publisher"
    assert e.keyword == ["data", "science"]
    assert e.landing_page == "https://example.com"
    assert e.theme == ["education", "research"]
    assert e.access_url == "https://data.example.com"
    assert e.raw_metadata["source"] == "test"


def test_catalog_entry_base_default_identifier():
    """Test CatalogEntryBase generates UUID identifier by default."""
    e = CatalogEntryBase()
    assert e.identifier is not None
    assert len(e.identifier) > 0  # UUID should be generated


def test_catalog_entry_base_default_raw_metadata():
    """Test CatalogEntryBase has empty dict for raw_metadata by default."""
    e = CatalogEntryBase(identifier="test")
    assert e.raw_metadata == {}


def test_column_relation_base_creation():
    """Test ColumnRelationBase instantiation."""
    r = ColumnRelationBase(catalog_column="title", correlation=0.95, metadata_column="dc.title")
    assert r.catalog_column == "title"
    assert r.correlation == 0.95
    assert r.metadata_column == "dc.title"


def test_column_relation_correlation_bounds():
    """Test ColumnRelationBase enforces correlation bounds (0.0-1.0)."""
    # Valid: 0.0
    r1 = ColumnRelationBase(catalog_column="title", correlation=0.0, metadata_column="dc.title")
    assert r1.correlation == 0.0

    # Valid: 1.0
    r2 = ColumnRelationBase(catalog_column="title", correlation=1.0, metadata_column="dc.title")
    assert r2.correlation == 1.0

    # Invalid: > 1.0
    with pytest.raises(ValidationError):
        ColumnRelationBase(catalog_column="title", correlation=1.5, metadata_column="dc.title")

    # Invalid: < 0.0
    with pytest.raises(ValidationError):
        ColumnRelationBase(catalog_column="title", correlation=-0.1, metadata_column="dc.title")


def test_column_relation_required_fields():
    """Test ColumnRelationBase requires all fields."""
    with pytest.raises(ValidationError):
        ColumnRelationBase(catalog_column="title", correlation=0.95)  # type: ignore - missing metadata_column

    with pytest.raises(ValidationError):
        ColumnRelationBase(correlation=0.95, metadata_column="dc.title")  # type: ignore - missing catalog_column
