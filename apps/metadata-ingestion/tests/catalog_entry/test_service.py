"""Tests for CatalogEntryService."""

import io
from datetime import date, datetime
from unittest.mock import MagicMock


from app.src.catalog_entry.model import CatalogEntry, CatalogEntryCreate, CatalogEntryUpdate


class TestCatalogEntryService:
    """Test cases for CatalogEntryService."""

    # ========================================================================
    # create_catalog_entry tests
    # ========================================================================

    def test_create_catalog_entry(self, catalog_entry_service, mock_db_session):
        """Should create catalog entry via repository."""
        catalog_entry = CatalogEntry(
            identifier="test-identifier",
            title="Test Title",
        )

        catalog_entry_service.repository.save.side_effect = lambda db, e: e

        result = catalog_entry_service.create_catalog_entry(mock_db_session, catalog_entry)

        assert result.identifier == "test-identifier"
        assert result.title == "Test Title"
        catalog_entry_service.repository.save.assert_called_once()

    # ========================================================================
    # create_catalog_entry_draft tests
    # ========================================================================

    def test_create_catalog_entry_draft(self, catalog_entry_service, mock_db_session):
        """Should create draft from CatalogEntryCreate DTO."""
        create_dto = CatalogEntryCreate(
            identifier="draft-identifier",
            ingested_at=datetime(2024, 1, 1),
            latest_snapshot_id="urn:wisenut:metadata:1234567890-abcdef123456",
        )

        catalog_entry_service.repository.save.side_effect = lambda db, e: e

        result = catalog_entry_service.create_catalog_entry_draft(mock_db_session, create_dto)

        assert isinstance(result, CatalogEntry)
        assert result.identifier == "draft-identifier"
        catalog_entry_service.repository.save.assert_called_once()

    # ========================================================================
    # update_catalog_entry tests
    # ========================================================================

    def test_update_catalog_entry_with_changes(self, catalog_entry_service, mock_db_session):
        """Should update entry when there are changes."""
        existing_entry = MagicMock(spec=CatalogEntry)
        existing_entry.id = 1
        existing_entry.title = "Old Title"

        update_dto = MagicMock(spec=CatalogEntryUpdate)
        update_dto.has_changes.return_value = True
        update_dto.model_dump_for_update.return_value = {"title": "New Title", "description": "New Desc"}

        catalog_entry_service.repository.select.return_value = existing_entry
        catalog_entry_service.repository.save.side_effect = lambda db, e: e

        result = catalog_entry_service.update_catalog_entry(mock_db_session, 1, update_dto)

        catalog_entry_service.repository.select.assert_called()
        catalog_entry_service.repository.save.assert_called_once()

    def test_update_catalog_entry_no_changes(self, catalog_entry_service, mock_db_session):
        """Should return existing entry when no changes."""
        existing_entry = MagicMock(spec=CatalogEntry)

        update_dto = MagicMock(spec=CatalogEntryUpdate)
        update_dto.has_changes.return_value = False

        catalog_entry_service.repository.select.return_value = existing_entry

        result = catalog_entry_service.update_catalog_entry(mock_db_session, 1, update_dto)

        assert result == existing_entry
        catalog_entry_service.repository.save.assert_not_called()

    # ========================================================================
    # get_catalog_entry tests
    # ========================================================================

    def test_get_catalog_entry(self, catalog_entry_service, mock_db_session):
        """Should get entry by ID."""
        expected = MagicMock(spec=CatalogEntry)
        expected.id = 1
        catalog_entry_service.repository.select.return_value = expected

        result = catalog_entry_service.get_catalog_entry(mock_db_session, 1)

        assert result == expected
        catalog_entry_service.repository.select.assert_called_once_with(mock_db_session, 1)

    # ========================================================================
    # get_catalog_entry_by_identifier tests
    # ========================================================================

    def test_get_catalog_entry_by_identifier(self, catalog_entry_service, mock_db_session):
        """Should get entry by identifier string."""
        expected = MagicMock(spec=CatalogEntry)
        expected.identifier = "test-id"
        catalog_entry_service.repository.select_by_identifier.return_value = expected

        result = catalog_entry_service.get_catalog_entry_by_identifier(mock_db_session, "test-id")

        assert result == expected
        catalog_entry_service.repository.select_by_identifier.assert_called_once_with(mock_db_session, "test-id")

    # ========================================================================
    # get_catalog_entries tests
    # ========================================================================

    def test_get_catalog_entries(self, catalog_entry_service, mock_db_session):
        """Should get multiple entries by IDs."""
        expected = [MagicMock(), MagicMock()]
        catalog_entry_service.repository.select_by_ids.return_value = expected

        result = catalog_entry_service.get_catalog_entries(mock_db_session, [1, 2])

        assert result == expected
        catalog_entry_service.repository.select_by_ids.assert_called_once_with(mock_db_session, [1, 2])

    def test_get_catalog_entries_empty_list(self, catalog_entry_service, mock_db_session):
        """Should handle empty ID list."""
        catalog_entry_service.repository.select_by_ids.return_value = []

        result = catalog_entry_service.get_catalog_entries(mock_db_session, [])

        assert result == []

    # ========================================================================
    # get_catalog_entries_by_identifier tests
    # ========================================================================

    def test_get_catalog_entries_by_identifier(self, catalog_entry_service, mock_db_session):
        """Should get multiple entries by identifiers."""
        expected = [MagicMock(), MagicMock()]
        catalog_entry_service.repository.select_by_identifiers.return_value = expected

        result = catalog_entry_service.get_catalog_entries_by_identifier(mock_db_session, ["id-1", "id-2"])

        assert result == expected

    # ========================================================================
    # get_catalog_entry_summary_by_identifier tests
    # ========================================================================

    def test_get_catalog_entry_summary_by_identifier(self, catalog_entry_service, mock_db_session):
        """Should get summaries by identifiers."""
        expected = [MagicMock(), MagicMock()]
        catalog_entry_service.repository.select_summaries_by_identifiers.return_value = expected

        result = catalog_entry_service.get_catalog_entry_summary_by_identifier(mock_db_session, ["id-1"])

        assert result == expected

    # ========================================================================
    # export_to_csv_stream tests
    # ========================================================================

    def test_export_to_csv_stream(self, catalog_entry_service, mock_db_session):
        """Should export data to CSV StringIO."""
        catalog_entry_service.repository.export_data_list.return_value = [
            {"id": 1, "title": "First"},
            {"id": 2, "title": "Second"},
        ]

        result = catalog_entry_service.export_to_csv_stream(mock_db_session, limit=100)

        assert isinstance(result, io.StringIO)
        csv_content = result.getvalue()
        assert "id" in csv_content
        assert "title" in csv_content
        assert "First" in csv_content
        assert "Second" in csv_content

    def test_export_to_csv_stream_empty(self, catalog_entry_service, mock_db_session):
        """Should handle empty data."""
        catalog_entry_service.repository.export_data_list.return_value = []

        result = catalog_entry_service.export_to_csv_stream(mock_db_session, limit=100)

        assert isinstance(result, io.StringIO)

    # ========================================================================
    # list_catalog tests
    # ========================================================================

    def test_list_catalog_with_limit(self, catalog_entry_service, mock_db_session):
        """Should pass limit to repository."""
        catalog_entry_service.repository.list_catalog_summary.return_value = []

        catalog_entry_service.list_catalog(mock_db_session, limit=50)

        catalog_entry_service.repository.list_catalog_summary.assert_called_once_with(mock_db_session, limit=50)

    def test_list_catalog_no_limit(self, catalog_entry_service, mock_db_session):
        """Should work without limit."""
        catalog_entry_service.repository.list_catalog_summary.return_value = []

        catalog_entry_service.list_catalog(mock_db_session, limit=None)

        catalog_entry_service.repository.list_catalog_summary.assert_called_once_with(mock_db_session, limit=None)

    # ========================================================================
    # search_catalog tests
    # ========================================================================

    def test_search_catalog_with_query(self, catalog_entry_service, mock_db_session):
        """Should search with query parameter."""
        mock_entry = MagicMock()
        mock_entry.model_dump.return_value = {
            "id": 1,
            "title": "Test",
            "issued": date(2024, 1, 1),
            "modified": date(2024, 1, 2),
            "ingested_at": datetime(2024, 1, 1, 10, 0),
            "updated_at": datetime(2024, 1, 2, 10, 0),
        }
        catalog_entry_service.repository.search_catalog.return_value = [mock_entry]

        result = catalog_entry_service.search_catalog(mock_db_session, query="test")

        assert len(result) == 1
        assert result[0]["issued"] == "2024-01-01"

    def test_search_catalog_with_keyword(self, catalog_entry_service, mock_db_session):
        """Should search with keyword filter."""
        catalog_entry_service.repository.search_catalog.return_value = []

        catalog_entry_service.search_catalog(mock_db_session, keyword="energy")

        catalog_entry_service.repository.search_catalog.assert_called_once_with(
            db=mock_db_session, query=None, keyword="energy"
        )

    def test_search_catalog_with_all_params_none(self, catalog_entry_service, mock_db_session):
        """Should search with all params None (returns all entries)."""
        catalog_entry_service.repository.search_catalog.return_value = []

        catalog_entry_service.search_catalog(mock_db_session)

        catalog_entry_service.repository.search_catalog.assert_called_once_with(
            db=mock_db_session, query=None, keyword=None
        )

    # ========================================================================
    # create_catalog_entry_bulk tests
    # ========================================================================

    def test_create_catalog_entry_bulk(self, catalog_entry_service, mock_db_session):
        """Should call repository create_bulk."""
        entries = [{"title": "First"}, {"title": "Second"}]

        catalog_entry_service.create_catalog_entry_bulk(mock_db_session, entries)

        catalog_entry_service.repository.create_bulk.assert_called_once_with(mock_db_session, entries)

    def test_create_catalog_entry_bulk_empty_list(self, catalog_entry_service, mock_db_session):
        """Should handle empty list for bulk create."""
        catalog_entry_service.create_catalog_entry_bulk(mock_db_session, [])

        catalog_entry_service.repository.create_bulk.assert_called_once_with(mock_db_session, [])

    # ========================================================================
    # update_catalog_entry_bulk tests
    # ========================================================================

    def test_update_catalog_entry_bulk(self, catalog_entry_service, mock_db_session):
        """Should call repository update_bulk."""
        entries = [{"id": 1, "title": "Updated First"}, {"id": 2, "title": "Updated Second"}]

        catalog_entry_service.update_catalog_entry_bulk(mock_db_session, entries)

        catalog_entry_service.repository.update_bulk.assert_called_once_with(mock_db_session, entries)
