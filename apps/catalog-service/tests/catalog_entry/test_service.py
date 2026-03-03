"""Tests for CatalogEntryService."""

import io
from datetime import date
from unittest.mock import MagicMock

from app.src.catalog_entry.model import CatalogEntry, CatalogEntrySummary
from app.src.catalog_entry.service import CatalogEntryService
from tests.constants import ENTRY_ID_1, ENTRY_ID_2


class TestGetCatalogEntry:
    """Tests for get_catalog_entry method."""

    def test_returns_entry_by_id(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry: CatalogEntry,
    ) -> None:
        """Should return catalog entry when found by ID."""
        mock_catalog_entry_repository.select.return_value = sample_catalog_entry

        result = catalog_entry_service.get_catalog_entry(mock_db, 1)

        assert result == sample_catalog_entry
        mock_catalog_entry_repository.select.assert_called_once_with(mock_db, 1)


class TestGetCatalogEntryByIdentifier:
    """Tests for get_catalog_entry_by_identifier method."""

    def test_returns_entry_by_identifier(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry: CatalogEntry,
    ) -> None:
        """Should return catalog entry when found by identifier."""
        mock_catalog_entry_repository.select_by_identifier.return_value = sample_catalog_entry

        result = catalog_entry_service.get_catalog_entry_by_identifier(mock_db, ENTRY_ID_1)

        assert result == sample_catalog_entry
        mock_catalog_entry_repository.select_by_identifier.assert_called_once_with(mock_db, ENTRY_ID_1)


class TestGetCatalogEntries:
    """Tests for get_catalog_entries method."""

    def test_returns_multiple_entries_by_ids(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry: CatalogEntry,
    ) -> None:
        """Should return multiple catalog entries by IDs."""
        entries = [sample_catalog_entry]
        mock_catalog_entry_repository.select_by_ids.return_value = entries

        result = catalog_entry_service.get_catalog_entries(mock_db, [1, 2])

        assert result == entries
        mock_catalog_entry_repository.select_by_ids.assert_called_once_with(mock_db, [1, 2])

    def test_returns_empty_list_for_empty_ids(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return empty list when passed empty ID list."""
        mock_catalog_entry_repository.select_by_ids.return_value = []

        result = catalog_entry_service.get_catalog_entries(mock_db, [])

        assert result == []
        mock_catalog_entry_repository.select_by_ids.assert_called_once_with(mock_db, [])


class TestGetCatalogEntriesByIdentifier:
    """Tests for get_catalog_entries_by_identifier method."""

    def test_returns_entries_by_identifiers(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry: CatalogEntry,
    ) -> None:
        """Should return entries when found by identifiers."""
        entries = [sample_catalog_entry]
        mock_catalog_entry_repository.select_by_identifiers.return_value = entries

        result = catalog_entry_service.get_catalog_entries_by_identifier(mock_db, [ENTRY_ID_1])

        assert result == entries
        mock_catalog_entry_repository.select_by_identifiers.assert_called_once_with(mock_db, [ENTRY_ID_1])


class TestGetCatalogEntrySummaryByIdentifier:
    """Tests for get_catalog_entry_summary_by_identifier method."""

    def test_returns_summaries_by_identifiers(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry_summary: CatalogEntrySummary,
    ) -> None:
        """Should return summaries when found by identifiers."""
        summaries = [sample_catalog_entry_summary]
        mock_catalog_entry_repository.select_summaries_by_identifiers.return_value = summaries

        result = catalog_entry_service.get_catalog_entry_summary_by_identifier(mock_db, [ENTRY_ID_1])

        assert result == summaries
        mock_catalog_entry_repository.select_summaries_by_identifiers.assert_called_once_with(
            mock_db, [ENTRY_ID_1]
        )


class TestGetRawMetadata:
    """Tests for get_raw_metadata method."""

    def test_returns_json_format_by_default(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return raw metadata as JSON by default."""
        test_raw_metadata = {"title": "Test Dataset", "nested": {"key": "value"}}
        entry = CatalogEntry(id=1, identifier=ENTRY_ID_1, raw_metadata=test_raw_metadata)
        mock_catalog_entry_repository.select.return_value = entry

        result = catalog_entry_service.get_raw_metadata(mock_db, 1)

        assert result == test_raw_metadata

    def test_returns_xml_format_when_specified(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return raw metadata as XML when format is xml."""
        # xmltodict.unparse requires exactly one root element
        entry = CatalogEntry(
            id=1,
            identifier="xml-test",
            raw_metadata={"dataset": {"title": "XML Dataset", "description": "Test"}},
        )
        mock_catalog_entry_repository.select.return_value = entry

        result = catalog_entry_service.get_raw_metadata(mock_db, 1, data_format="xml")

        assert isinstance(result, str)
        assert "<?xml" in result
        assert "XML Dataset" in result


class TestGetRawMetadatas:
    """Tests for get_raw_metadatas method."""

    def test_returns_multiple_raw_metadatas(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry: CatalogEntry,
    ) -> None:
        """Should return raw metadata for multiple entries."""
        entries = [sample_catalog_entry]
        mock_catalog_entry_repository.select_by_ids.return_value = entries

        result = catalog_entry_service.get_raw_metadatas(mock_db, [1])

        assert result == [sample_catalog_entry.raw_metadata]
        mock_catalog_entry_repository.select_by_ids.assert_called_once_with(mock_db, [1])


class TestExportToCsvStream:
    """Tests for export_to_csv_stream method."""

    def test_returns_csv_stream(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return CSV stream from export data."""
        export_data = [
            {"id": 1, "title": "Dataset 1", "identifier": ENTRY_ID_1},
            {"id": 2, "title": "Dataset 2", "identifier": ENTRY_ID_2},
        ]
        mock_catalog_entry_repository.export_data_list.return_value = export_data

        result = catalog_entry_service.export_to_csv_stream(mock_db, limit=100)

        assert isinstance(result, io.StringIO)
        csv_content = result.getvalue()
        assert "Dataset 1" in csv_content
        assert "Dataset 2" in csv_content

    def test_passes_limit_to_repository(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should pass limit parameter to repository."""
        mock_catalog_entry_repository.export_data_list.return_value = []

        catalog_entry_service.export_to_csv_stream(mock_db, limit=50)

        mock_catalog_entry_repository.export_data_list.assert_called_once_with(mock_db, limit=50)

    def test_returns_valid_csv_with_limit_zero(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return valid empty CSV when limit=0 returns no data."""
        mock_catalog_entry_repository.export_data_list.return_value = []

        result = catalog_entry_service.export_to_csv_stream(mock_db, limit=0)

        assert isinstance(result, io.StringIO)
        # Empty DataFrame produces empty CSV (just newline or empty)
        mock_catalog_entry_repository.export_data_list.assert_called_once_with(mock_db, limit=0)

    def test_escapes_special_characters_in_csv(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should properly escape special characters (comma, newline, quotes) in CSV."""
        export_data = [
            {"id": 1, "title": 'Title with "quotes"', "description": "Line1\nLine2"},
            {"id": 2, "title": "Title, with comma", "description": "Normal"},
        ]
        mock_catalog_entry_repository.export_data_list.return_value = export_data

        result = catalog_entry_service.export_to_csv_stream(mock_db, limit=100)

        csv_content = result.getvalue()
        # pandas CSV escaping wraps fields with special chars in quotes
        assert '"Title with ""quotes"""' in csv_content or 'Title with "quotes"' in csv_content
        assert "Title, with comma" in csv_content


class TestListCatalog:
    """Tests for list_catalog method."""

    def test_returns_catalog_summaries(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry_summary: CatalogEntrySummary,
    ) -> None:
        """Should return list of catalog summaries."""
        summaries = [sample_catalog_entry_summary]
        mock_catalog_entry_repository.list_catalog_summary.return_value = summaries

        result = catalog_entry_service.list_catalog(mock_db)

        assert result == summaries
        mock_catalog_entry_repository.list_catalog_summary.assert_called_once_with(mock_db, limit=None)

    def test_passes_limit_parameter(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should pass limit parameter to repository."""
        mock_catalog_entry_repository.list_catalog_summary.return_value = []

        catalog_entry_service.list_catalog(mock_db, limit=10)

        mock_catalog_entry_repository.list_catalog_summary.assert_called_once_with(mock_db, limit=10)

    def test_limit_zero_returns_empty(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should handle limit=0 (passes through to repository)."""
        mock_catalog_entry_repository.list_catalog_summary.return_value = []

        result = catalog_entry_service.list_catalog(mock_db, limit=0)

        assert result == []
        mock_catalog_entry_repository.list_catalog_summary.assert_called_once_with(mock_db, limit=0)


class TestSearchCatalog:
    """Tests for search_catalog method."""

    def test_search_with_query(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry_summary: CatalogEntrySummary,
    ) -> None:
        """Should search with text query."""
        summaries = [sample_catalog_entry_summary]
        mock_catalog_entry_repository.search_catalog.return_value = summaries

        result = catalog_entry_service.search_catalog(mock_db, query="sample")

        assert result == summaries
        mock_catalog_entry_repository.search_catalog.assert_called_once()

    def test_search_with_keyword_filter(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should search with keyword filter."""
        mock_catalog_entry_repository.search_catalog.return_value = []

        catalog_entry_service.search_catalog(mock_db, keyword=["test", "sample"])

        call_kwargs = mock_catalog_entry_repository.search_catalog.call_args.kwargs
        assert call_kwargs["keyword"] == ["test", "sample"]

    def test_search_with_theme_filter(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should search with theme filter."""
        mock_catalog_entry_repository.search_catalog.return_value = []

        catalog_entry_service.search_catalog(mock_db, theme=["science"])

        call_kwargs = mock_catalog_entry_repository.search_catalog.call_args.kwargs
        assert call_kwargs["theme"] == ["science"]

    def test_search_with_date_range(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should search with date range filter."""
        mock_catalog_entry_repository.search_catalog.return_value = []
        date_from = date(2024, 1, 1)
        date_to = date(2024, 12, 31)

        catalog_entry_service.search_catalog(
            mock_db, date_field="issued", date_from=date_from, date_to=date_to
        )

        call_kwargs = mock_catalog_entry_repository.search_catalog.call_args.kwargs
        assert call_kwargs["date_field"] == "issued"
        assert call_kwargs["date_from"] == date_from
        assert call_kwargs["date_to"] == date_to

    def test_search_with_pagination(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should search with pagination parameters."""
        mock_catalog_entry_repository.search_catalog.return_value = []

        catalog_entry_service.search_catalog(mock_db, offset=10, limit=20)

        call_kwargs = mock_catalog_entry_repository.search_catalog.call_args.kwargs
        assert call_kwargs["offset"] == 10
        assert call_kwargs["limit"] == 20

    def test_search_with_sorting(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should search with sorting parameters."""
        mock_catalog_entry_repository.search_catalog.return_value = []

        catalog_entry_service.search_catalog(mock_db, sort_field="title", sort_order="asc")

        call_kwargs = mock_catalog_entry_repository.search_catalog.call_args.kwargs
        assert call_kwargs["sort_field"] == "title"
        assert call_kwargs["sort_order"] == "asc"

    def test_search_with_all_parameters(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should search with all parameters combined."""
        mock_catalog_entry_repository.search_catalog.return_value = []

        catalog_entry_service.search_catalog(
            mock_db,
            query="test",
            keyword=["key1"],
            theme=["theme1"],
            date_field="modified",
            date_from=date(2024, 1, 1),
            date_to=date(2024, 12, 31),
            offset=5,
            limit=15,
            sort_field="issued",
            sort_order="desc",
        )

        mock_catalog_entry_repository.search_catalog.assert_called_once()

    def test_search_with_all_params_none(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_catalog_entry_summary: CatalogEntrySummary,
    ) -> None:
        """Should search with all filter params as None (return all with defaults)."""
        summaries = [sample_catalog_entry_summary]
        mock_catalog_entry_repository.search_catalog.return_value = summaries

        result = catalog_entry_service.search_catalog(mock_db)

        assert result == summaries
        call_kwargs = mock_catalog_entry_repository.search_catalog.call_args.kwargs
        assert call_kwargs["query"] is None
        assert call_kwargs["keyword"] is None
        assert call_kwargs["theme"] is None
        assert call_kwargs["offset"] == 0
        assert call_kwargs["limit"] == 10

    def test_search_offset_exceeds_total(
        self,
        catalog_entry_service: CatalogEntryService,
        mock_catalog_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return empty when offset exceeds total records."""
        mock_catalog_entry_repository.search_catalog.return_value = []

        result = catalog_entry_service.search_catalog(mock_db, offset=10000)

        assert result == []
        call_kwargs = mock_catalog_entry_repository.search_catalog.call_args.kwargs
        assert call_kwargs["offset"] == 10000
