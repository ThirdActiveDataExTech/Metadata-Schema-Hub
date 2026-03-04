"""Integration tests for CatalogEntryRepository."""

import pytest
from sqlmodel import Session

from app.src.catalog_entry.exceptions import CatalogEntryNotFoundError
from app.src.catalog_entry.model import CatalogEntry
from app.src.catalog_entry.repository import CatalogEntryRepository
from tests.constants import NONEXISTENT_ID, NONEXISTENT_IDENTIFIER


class TestSave:
    """Tests for save method."""

    def test_save_new_entry(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should save new entry and return with ID after flush."""
        entry = CatalogEntry(
            identifier="new-entry",
            title="New Dataset",
            raw_metadata={"test": "data"},
        )

        result = catalog_entry_repository.save(db, entry)
        db.flush()  # Flush to get auto-generated ID

        assert result.id is not None
        assert result.identifier == entry.identifier
        assert result.title == entry.title

    def test_save_updates_existing(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should update existing entry."""
        new_entry_title = "Updated Title"
        entry = sample_catalog_entries[0]
        entry.title = new_entry_title

        result = catalog_entry_repository.save(db, entry)

        assert result.title == new_entry_title
        assert result.id == entry.id


class TestSelect:
    """Tests for select method."""

    def test_select_existing(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return entry when found."""
        entry = sample_catalog_entries[0]
        result = catalog_entry_repository.select(db, entry.id)

        assert result.id == entry.id
        assert result.identifier == entry.identifier

    def test_select_nonexistent_raises(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should raise CatalogEntryNotFoundError."""
        with pytest.raises(CatalogEntryNotFoundError):
            catalog_entry_repository.select(db, NONEXISTENT_ID)


class TestSelectByIdentifier:
    """Tests for select_by_identifier method."""

    def test_select_by_identifier(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return entry by identifier."""
        entry = sample_catalog_entries[1]
        result = catalog_entry_repository.select_by_identifier(db, entry.identifier)

        assert result.identifier == entry.identifier
        assert result.title == entry.title

    def test_select_nonexistent_raises(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should raise CatalogEntryNotFoundError."""
        with pytest.raises(CatalogEntryNotFoundError):
            catalog_entry_repository.select_by_identifier(db, NONEXISTENT_IDENTIFIER)


class TestSelectByIds:
    """Tests for select_by_ids method."""

    def test_select_multiple(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return entries by IDs."""
        target_entries = sample_catalog_entries[:2]
        ids = [e.id for e in target_entries]
        result = catalog_entry_repository.select_by_ids(db, ids)

        assert len(result) == len(target_entries)

    def test_select_empty_list(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should return empty list for empty IDs."""
        result = catalog_entry_repository.select_by_ids(db, [])
        assert result == []


class TestSelectByIdentifiers:
    """Tests for select_by_identifiers method."""

    def test_select_multiple(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return entries by identifiers."""
        target_entries = [sample_catalog_entries[0], sample_catalog_entries[2]]
        identifiers = [e.identifier for e in target_entries]
        result = catalog_entry_repository.select_by_identifiers(db, identifiers)
        assert len(result) == len(target_entries)


class TestSelectSummariesByIdentifiers:
    """Tests for select_summaries_by_identifiers method."""

    def test_returns_summaries(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return summary objects."""
        entry = sample_catalog_entries[0]
        result = catalog_entry_repository.select_summaries_by_identifiers(
            db, [entry.identifier]
        )

        assert len(result) == 1
        assert result[0].identifier == entry.identifier


class TestListCatalogSummary:
    """Tests for list_catalog_summary method."""

    def test_list_all(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return all entries."""
        result = catalog_entry_repository.list_catalog_summary(db)
        assert len(result) == len(sample_catalog_entries)

    def test_list_with_limit(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should respect limit."""
        limit = 2
        result = catalog_entry_repository.list_catalog_summary(db, limit=limit)
        assert len(result) == limit


class TestSearchCatalog:
    """Tests for search_catalog method."""

    def test_search_with_query(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should search by text query."""
        target_entry = sample_catalog_entries[0]
        # Extract unique search term from target entry's title
        search_term = target_entry.title.split()[0]  # "First" from "First Dataset"
        result = catalog_entry_repository.search_catalog(db, query=search_term)

        assert len(result) == 1
        assert result[0].title == target_entry.title

    def test_search_no_filters(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return all when no filters."""
        result = catalog_entry_repository.search_catalog(db)
        assert len(result) == len(sample_catalog_entries)


class TestCreateBulk:
    """Tests for create_bulk method."""

    def test_create_multiple_entries(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should create multiple entries."""
        creates = [
            {
                "identifier": "bulk-001",
                "title": "Bulk Entry 1",
                "raw_metadata": {},
            },
            {
                "identifier": "bulk-002",
                "title": "Bulk Entry 2",
                "raw_metadata": {},
            },
        ]

        catalog_entry_repository.create_bulk(db, creates)

        # Verify entries were created
        result = catalog_entry_repository.select_by_identifiers(
            db, ["bulk-001", "bulk-002"]
        )
        assert len(result) == 2

    def test_create_bulk_empty_list(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should handle empty list."""
        catalog_entry_repository.create_bulk(db, [])
        # No error should be raised


class TestUpdateBulk:
    """Tests for update_bulk method."""

    def test_update_multiple_entries(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should update multiple entries."""
        entry1, entry2 = sample_catalog_entries[0], sample_catalog_entries[1]
        updated_title_1 = f"Updated {entry1.title}"
        updated_title_2 = f"Updated {entry2.title}"
        updates = [
            {"id": entry1.id, "title": updated_title_1},
            {"id": entry2.id, "title": updated_title_2},
        ]

        catalog_entry_repository.update_bulk(db, updates)
        db.commit()

        # Verify updates
        result1 = catalog_entry_repository.select(db, entry1.id)
        result2 = catalog_entry_repository.select(db, entry2.id)

        assert result1.title == updated_title_1
        assert result2.title == updated_title_2
