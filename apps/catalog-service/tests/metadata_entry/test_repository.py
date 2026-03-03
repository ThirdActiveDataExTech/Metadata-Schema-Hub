"""Integration tests for MetadataEntryRepository."""

import pytest
from sqlmodel import Session

from app.src.metadata_entry.model import MetadataEntry
from app.src.metadata_entry.repository import MetadataEntryRepository
from tests.constants import METADATA_ID_1, METADATA_ID_2


class TestSelectMetadataEntry:
    """Tests for select_metadata_entry method."""

    def test_select_by_metadata_id(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return all entries for given metadata_id."""
        result = metadata_entry_repository.select_metadata_entry(db, METADATA_ID_1)

        assert len(result) == 2
        schemas = {e.metadata_schema for e in result}
        assert schemas == {"dct:title", "dct:description"}

    def test_select_nonexistent_metadata_id(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should return empty list for non-existent metadata_id."""
        result = metadata_entry_repository.select_metadata_entry(db, "nonexistent")
        assert result == []


class TestSelectMetadataEntriesByMetadataIds:
    """Tests for select_metadata_entries_by_metadata_ids method."""

    def test_select_by_multiple_ids(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return entries for multiple metadata IDs."""
        result = metadata_entry_repository.select_metadata_entries_by_metadata_ids(
            db, [METADATA_ID_1, METADATA_ID_2]
        )

        assert len(result) == 4  # 2 + 2 entries

    def test_select_empty_list(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should return empty list for empty ID list."""
        result = metadata_entry_repository.select_metadata_entries_by_metadata_ids(
            db, []
        )
        assert result == []


class TestSearchMetadata:
    """Tests for search_metadata method."""

    def test_search_with_query(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should search by value text (ILIKE on value and metadata_schema)."""
        result = metadata_entry_repository.search_metadata(db, query="Sample")

        # Matches: "Sample Title", "Sample Description", "test,sample"
        assert len(result) == 3

    def test_search_with_schema_filter(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should filter by schema."""
        result = metadata_entry_repository.search_metadata(db, schema="dct:title")

        assert len(result) == 2
        assert all(e.metadata_schema == "dct:title" for e in result)

    def test_search_with_metadata_id_filter(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should filter by metadata_id."""
        result = metadata_entry_repository.search_metadata(db, metadata_id=METADATA_ID_1)

        assert len(result) == 2
        assert all(e.metadata_id == METADATA_ID_1 for e in result)

    def test_search_with_multiple_filters(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should apply multiple filters (AND condition)."""
        entry = sample_metadata_entries[0]  # dct:title with METADATA_ID_1
        result = metadata_entry_repository.search_metadata(
            db, schema=entry.metadata_schema, metadata_id=entry.metadata_id
        )

        assert len(result) == 1
        assert result[0].value == entry.value

    def test_search_no_filters(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return all entries when no filters."""
        result = metadata_entry_repository.search_metadata(db)
        assert len(result) == 4


class TestListMetadataSummary:
    """Tests for list_metadata_summary method."""

    def test_list_all(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return all entries."""
        result = metadata_entry_repository.list_metadata_summary(db)
        assert len(result) == 4

    def test_list_with_limit(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should respect limit parameter."""
        result = metadata_entry_repository.list_metadata_summary(db, limit=2)
        assert len(result) == 2

    def test_list_empty_table(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should return empty list when no entries."""
        result = metadata_entry_repository.list_metadata_summary(db)
        assert result == []


class TestSelectDistinctMetadataSchemas:
    """Tests for select_distinct_metadata_schemas method."""

    def test_select_distinct_schemas(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return distinct schemas for given metadata IDs."""
        result = metadata_entry_repository.select_distinct_metadata_schemas(
            db, [METADATA_ID_1]
        )

        assert set(result) == {"dct:title", "dct:description"}

    def test_select_distinct_across_ids(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return distinct schemas across multiple metadata IDs."""
        result = metadata_entry_repository.select_distinct_metadata_schemas(
            db, [METADATA_ID_1, METADATA_ID_2]
        )

        assert set(result) == {"dct:title", "dct:description", "dcat:keyword"}

    def test_select_distinct_empty_list(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should return empty list for empty ID list."""
        result = metadata_entry_repository.select_distinct_metadata_schemas(db, [])
        assert result == []
