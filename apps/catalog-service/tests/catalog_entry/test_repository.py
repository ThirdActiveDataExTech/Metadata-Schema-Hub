"""Integration tests for CatalogEntryRepository."""

import pytest
from sqlmodel import Session

from app.src.catalog_entry.exceptions import CatalogEntryNotFoundError
from app.src.catalog_entry.model import CatalogEntry
from app.src.catalog_entry.repository import CatalogEntryRepository


class TestSelect:
    """Tests for select method."""

    def test_select_existing_entry(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return entry when found by ID."""
        entry = sample_catalog_entries[0]
        result = catalog_entry_repository.select(db, entry.id)

        assert result.id == entry.id
        assert result.identifier == entry.identifier
        assert result.title == entry.title

    def test_select_nonexistent_entry_raises(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should raise CatalogEntryNotFoundError for non-existent ID."""
        with pytest.raises(CatalogEntryNotFoundError):
            catalog_entry_repository.select(db, 99999)


class TestSelectByIdentifier:
    """Tests for select_by_identifier method."""

    def test_select_by_identifier_existing(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return entry when found by identifier."""
        entry = sample_catalog_entries[1]
        result = catalog_entry_repository.select_by_identifier(db, entry.identifier)

        assert result.identifier == entry.identifier
        assert result.title == entry.title

    def test_select_by_identifier_nonexistent_raises(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should raise CatalogEntryNotFoundError for non-existent identifier."""
        with pytest.raises(CatalogEntryNotFoundError):
            catalog_entry_repository.select_by_identifier(db, "nonexistent-id")


class TestSelectByIds:
    """Tests for select_by_ids method."""

    def test_select_by_ids_multiple(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return multiple entries by IDs."""
        entry0 = sample_catalog_entries[0]
        entry2 = sample_catalog_entries[2]
        ids = [entry0.id, entry2.id]
        result = catalog_entry_repository.select_by_ids(db, ids)

        assert len(result) == 2
        identifiers = {e.identifier for e in result}
        assert identifiers == {entry0.identifier, entry2.identifier}

    def test_select_by_ids_empty_list(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should return empty list for empty ID list."""
        result = catalog_entry_repository.select_by_ids(db, [])
        assert result == []

    def test_select_by_ids_partial_match(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return only existing entries when some IDs don't exist."""
        entry = sample_catalog_entries[0]
        ids = [entry.id, 99999]
        result = catalog_entry_repository.select_by_ids(db, ids)

        assert len(result) == 1
        assert result[0].identifier == entry.identifier


class TestSelectByIdentifiers:
    """Tests for select_by_identifiers method."""

    def test_select_by_identifiers_multiple(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return entries by identifiers."""
        result = catalog_entry_repository.select_by_identifiers(
            db, ["entry-001", "entry-003"]
        )

        assert len(result) == 2

    def test_select_by_identifiers_empty(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should return empty list for empty identifier list."""
        result = catalog_entry_repository.select_by_identifiers(db, [])
        assert result == []


class TestSelectSummariesByIdentifiers:
    """Tests for select_summaries_by_identifiers method."""

    def test_returns_summaries(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return CatalogEntrySummary objects."""
        entry = sample_catalog_entries[0]
        result = catalog_entry_repository.select_summaries_by_identifiers(
            db, [entry.identifier]
        )

        assert len(result) == 1
        summary = result[0]
        assert summary.identifier == entry.identifier
        assert summary.title == entry.title
        assert summary.issued == str(entry.issued)


class TestListCatalogSummary:
    """Tests for list_catalog_summary method."""

    def test_list_all(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return all entries when no limit."""
        result = catalog_entry_repository.list_catalog_summary(db)
        assert len(result) == 3

    def test_list_with_limit(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should respect limit parameter."""
        result = catalog_entry_repository.list_catalog_summary(db, limit=2)
        assert len(result) == 2

    def test_list_ordered_by_id_desc(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return entries ordered by ID descending."""
        result = catalog_entry_repository.list_catalog_summary(db)

        # Most recent (highest ID) first
        assert result[0].identifier == sample_catalog_entries[2].identifier
        assert result[-1].identifier == sample_catalog_entries[0].identifier

    def test_list_empty_table(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should return empty list when no entries exist."""
        result = catalog_entry_repository.list_catalog_summary(db)
        assert result == []


class TestExportDataList:
    """Tests for export_data_list method."""

    def test_export_all_entries(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should export all entries as dicts."""
        result = catalog_entry_repository.export_data_list(db)

        assert len(result) == 3
        assert all(isinstance(item, dict) for item in result)

    def test_export_with_limit(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should respect limit parameter."""
        result = catalog_entry_repository.export_data_list(db, limit=1)
        assert len(result) == 1

    def test_export_empty_returns_none(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
    ) -> None:
        """Should return None when no data."""
        result = catalog_entry_repository.export_data_list(db)
        assert result is None

    def test_export_converts_dates_to_strings(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should convert date fields to strings."""
        result = catalog_entry_repository.export_data_list(db, limit=1)

        item = result[0]
        if item.get("issued"):
            assert isinstance(item["issued"], str)
        if item.get("modified"):
            assert isinstance(item["modified"], str)


class TestSearchCatalog:
    """Tests for search_catalog method."""

    def test_search_with_text_query(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should search by title/description text."""
        entry = sample_catalog_entries[0]
        result = catalog_entry_repository.search_catalog(db, query="First")

        assert len(result) == 1
        assert result[0].title == entry.title

    def test_search_with_pagination(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should apply offset and limit."""
        result = catalog_entry_repository.search_catalog(db, offset=1, limit=1)
        assert len(result) == 1

    def test_search_with_sorting(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should sort by specified field and order."""
        result = catalog_entry_repository.search_catalog(
            db, sort_field="title", sort_order="asc", limit=10
        )

        titles = [r.title for r in result]
        assert titles == sorted(titles)

    def test_search_with_date_range(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should filter by date range."""
        from datetime import date

        entry = sample_catalog_entries[1]  # entry-002 with issued=2024-02-01
        result = catalog_entry_repository.search_catalog(
            db,
            date_field="issued",
            date_from=date(2024, 2, 1),
            date_to=date(2024, 2, 28),
            limit=10,
        )

        assert len(result) == 1
        assert result[0].identifier == entry.identifier

    def test_search_returns_empty_for_no_match(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should return empty list when no matches."""
        result = catalog_entry_repository.search_catalog(db, query="nonexistent_xyz")
        assert result == []

    def test_search_default_pagination(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should use default pagination (offset=0, limit=10)."""
        result = catalog_entry_repository.search_catalog(db)
        assert len(result) == 3  # All entries, default limit=10

    def test_search_with_keyword_filter(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should filter by keyword (PostgreSQL ARRAY feature)."""
        result = catalog_entry_repository.search_catalog(db, keyword=["science"])
        assert len(result) == 2

    def test_search_with_theme_filter(
        self,
        db: Session,
        catalog_entry_repository: CatalogEntryRepository,
        sample_catalog_entries: list[CatalogEntry],
    ) -> None:
        """Should filter by theme (PostgreSQL ARRAY feature)."""
        result = catalog_entry_repository.search_catalog(db, theme=["research"])
        assert len(result) == 2
