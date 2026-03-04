"""Integration tests for MetadataEntryRepository."""

import pytest
from sqlmodel import Session

from app.src.metadata_entry.model import MetadataEntry
from app.src.metadata_entry.repository import MetadataEntryRepository
from tests.constants import METADATA_ID_1, METADATA_ID_2, NONEXISTENT_IDENTIFIER


class TestSave:
    """Tests for save method."""

    def test_save_entries(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should save multiple entries and return with IDs."""
        entries = [
            MetadataEntry(
                metadata_schema="dct:title",
                value="New Title",
                metadata_id="new-METADATA_ID_1",
            ),
            MetadataEntry(
                metadata_schema="dct:description",
                value="New Description",
                metadata_id="new-METADATA_ID_1",
            ),
        ]

        result = metadata_entry_repository.save(db, entries)

        assert len(result) == 2
        assert all(e.id is not None for e in result)


class TestCreateBulk:
    """Tests for create_bulk method."""

    def test_create_bulk_entries(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should create multiple entries via bulk insert."""
        creates = [
            {
                "metadata_schema": "dct:title",
                "value": "Bulk Title",
                "metadata_id": "bulk-METADATA_ID_1",
            },
            {
                "metadata_schema": "dct:description",
                "value": "Bulk Description",
                "metadata_id": "bulk-METADATA_ID_1",
            },
        ]

        metadata_entry_repository.create_bulk(db, creates)

        # Verify
        result = metadata_entry_repository.select_metadata_entry(db, "bulk-METADATA_ID_1")
        assert len(result) == 2

    def test_create_bulk_empty(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should handle empty list."""
        metadata_entry_repository.create_bulk(db, [])


class TestSelectMetadataEntry:
    """Tests for select_metadata_entry method."""

    def test_select_by_metadata_id(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return entries for metadata_id."""
        result = metadata_entry_repository.select_metadata_entry(db, METADATA_ID_1)

        assert len(result) == 2
        schemas = {e.metadata_schema for e in result}
        assert schemas == {"dct:title", "dct:description"}

    def test_select_nonexistent(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should return empty list."""
        result = metadata_entry_repository.select_metadata_entry(db, NONEXISTENT_IDENTIFIER)
        assert result == []

    def test_select_with_empty_string_metadata_id(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should return empty list for empty string metadata_id."""
        result = metadata_entry_repository.select_metadata_entry(db, "")
        assert result == []


class TestSelectMetadataEntriesByMetadataIds:
    """Tests for select_metadata_entries_by_metadata_ids method."""

    def test_select_multiple_ids(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return entries for multiple IDs."""
        target_ids = [METADATA_ID_1, METADATA_ID_2]
        result = metadata_entry_repository.select_metadata_entries_by_metadata_ids(
            db, target_ids
        )
        # All sample_metadata_entries belong to METADATA_ID_1 or METADATA_ID_2
        assert len(result) == len(sample_metadata_entries)


class TestSearchMetadata:
    """Tests for search_metadata method."""

    def test_search_by_query(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should search by value text (ILIKE on value and metadata_schema)."""
        search_term = "Sample"
        result = metadata_entry_repository.search_metadata(db, query=search_term)
        # Count entries containing "Sample" in value (case-insensitive)
        expected_count = sum(
            1 for e in sample_metadata_entries if search_term.lower() in e.value.lower()
        )
        assert len(result) == expected_count

    def test_search_by_schema(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should filter by schema."""
        target_schema = "dct:title"
        result = metadata_entry_repository.search_metadata(db, schema=target_schema)
        expected_count = sum(
            1 for e in sample_metadata_entries if e.metadata_schema == target_schema
        )
        assert len(result) == expected_count

    def test_search_combined_filters(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should apply multiple filters."""
        target_entry = sample_metadata_entries[0]
        result = metadata_entry_repository.search_metadata(
            db, schema=target_entry.metadata_schema, metadata_id=target_entry.metadata_id
        )
        assert len(result) == 1


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
        assert len(result) == len(sample_metadata_entries)

    def test_list_with_limit(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should respect limit."""
        limit = 2
        result = metadata_entry_repository.list_metadata_summary(db, limit=limit)
        assert len(result) == limit


class TestSelectDistinctMetadataSchemas:
    """Tests for select_distinct_metadata_schemas method."""

    def test_select_distinct(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return distinct schemas."""
        target_ids = [METADATA_ID_1, METADATA_ID_2]
        result = metadata_entry_repository.select_distinct_metadata_schemas(db, target_ids)
        expected_schemas = {
            e.metadata_schema for e in sample_metadata_entries if e.metadata_id in target_ids
        }
        assert set(result) == expected_schemas


class TestGetAllDistinctMetadataSchemas:
    """Tests for get_all_distinct_metadata_schemas method."""

    def test_get_all_distinct(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
        sample_metadata_entries: list[MetadataEntry],
    ) -> None:
        """Should return all distinct schemas."""
        result = metadata_entry_repository.get_all_distinct_metadata_schemas(db)
        expected_schemas = {e.metadata_schema for e in sample_metadata_entries}
        assert set(result) == expected_schemas

    def test_get_all_empty(
        self,
        db: Session,
        metadata_entry_repository: MetadataEntryRepository,
    ) -> None:
        """Should return empty list when no entries."""
        result = metadata_entry_repository.get_all_distinct_metadata_schemas(db)
        assert result == []
