"""Tests for MetadataEntryService."""

from datetime import datetime
from unittest.mock import MagicMock


from app.src.metadata_entry.model import MetadataCreate, MetadataEntry, MetadataSchema


class TestMetadataEntryService:
    """Test cases for MetadataEntryService."""

    # ========================================================================
    # create tests
    # ========================================================================

    def test_create_converts_schemas_to_entries(self, metadata_entry_service, mock_db_session):
        """Should convert MetadataCreate schemas to MetadataEntry list."""
        metadata_create = MetadataCreate(
            metadata_id="test-metadata-001",
            metadata_schemas=[
                MetadataSchema(metadata_schema="name", value="Test Dataset"),
                MetadataSchema(metadata_schema="description", value="Test Description"),
            ],
        )

        # Mock repository to return what was passed
        metadata_entry_service.repository.save.side_effect = lambda db, entries: entries

        result = metadata_entry_service.create(mock_db_session, metadata_create)

        assert len(result) == 2
        assert all(isinstance(e, MetadataEntry) for e in result)
        assert all(e.metadata_id == "test-metadata-001" for e in result)

    def test_create_calls_repository_save(self, metadata_entry_service, mock_db_session):
        """Should call repository.save with converted entries."""
        metadata_create = MetadataCreate(
            metadata_id="test-id",
            metadata_schemas=[MetadataSchema(metadata_schema="key", value="value")],
        )

        metadata_entry_service.create(mock_db_session, metadata_create)

        metadata_entry_service.repository.save.assert_called_once()
        call_args = metadata_entry_service.repository.save.call_args
        assert call_args[0][0] == mock_db_session

    # ========================================================================
    # create_bulk tests
    # ========================================================================

    def test_create_bulk_flattens_all_schemas(self, metadata_entry_service, mock_db_session):
        """Should flatten all MetadataCreate into single bulk insert."""
        metadata_creates = [
            MetadataCreate(
                metadata_id="id-1",
                metadata_schemas=[
                    MetadataSchema(metadata_schema="name", value="First"),
                    MetadataSchema(metadata_schema="desc", value="First Desc"),
                ],
            ),
            MetadataCreate(
                metadata_id="id-2",
                metadata_schemas=[MetadataSchema(metadata_schema="name", value="Second")],
            ),
        ]

        metadata_entry_service.create_bulk(mock_db_session, metadata_creates)

        metadata_entry_service.repository.create_bulk.assert_called_once()
        call_args = metadata_entry_service.repository.create_bulk.call_args
        dumps = call_args[0][1]
        assert len(dumps) == 3  # 2 + 1 schemas total

    def test_create_bulk_empty_list(self, metadata_entry_service, mock_db_session):
        """Should handle empty list."""
        metadata_entry_service.create_bulk(mock_db_session, [])

        metadata_entry_service.repository.create_bulk.assert_called_once()
        call_args = metadata_entry_service.repository.create_bulk.call_args
        assert call_args[0][1] == []

    # ========================================================================
    # select_metadata tests
    # ========================================================================

    def test_select_metadata_returns_entries(self, metadata_entry_service, mock_db_session):
        """Should return entries for metadata_id."""
        expected_entries = [
            MagicMock(metadata_id="test-id", metadata_schema="name", value="Test"),
            MagicMock(metadata_id="test-id", metadata_schema="desc", value="Desc"),
        ]
        metadata_entry_service.repository.select_metadata_entry.return_value = expected_entries

        result = metadata_entry_service.select_metadata(mock_db_session, "test-id")

        assert result == expected_entries
        metadata_entry_service.repository.select_metadata_entry.assert_called_once_with(mock_db_session, "test-id")

    def test_select_metadata_not_found_returns_empty(self, metadata_entry_service, mock_db_session):
        """Should return empty list when metadata_id not found."""
        metadata_entry_service.repository.select_metadata_entry.return_value = []

        result = metadata_entry_service.select_metadata(mock_db_session, "nonexistent-id")

        assert result == []

    # ========================================================================
    # select_metadata_schemas_distinct tests
    # ========================================================================

    def test_select_metadata_schemas_distinct(self, metadata_entry_service, mock_db_session):
        """Should return unique schemas across metadata_ids."""
        metadata_entry_service.repository.select_distinct_metadata_schemas.return_value = ["name", "description", "keywords"]

        result = metadata_entry_service.select_metadata_schemas_distinct(mock_db_session, ["id-1", "id-2"])

        assert result == ["name", "description", "keywords"]
        metadata_entry_service.repository.select_distinct_metadata_schemas.assert_called_once_with(
            mock_db_session, ["id-1", "id-2"]
        )

    # ========================================================================
    # select_metadata_bulk tests
    # ========================================================================

    def test_select_metadata_bulk(self, metadata_entry_service, mock_db_session):
        """Should return entries for multiple metadata_ids."""
        expected = [MagicMock(), MagicMock()]
        metadata_entry_service.repository.select_metadata_entries_by_metadata_ids.return_value = expected

        result = metadata_entry_service.select_metadata_bulk(mock_db_session, ["id-1", "id-2"])

        assert result == expected
        metadata_entry_service.repository.select_metadata_entries_by_metadata_ids.assert_called_once()

    # ========================================================================
    # list_metadata tests
    # ========================================================================

    def test_list_metadata_with_limit(self, metadata_entry_service, mock_db_session):
        """Should pass limit to repository."""
        metadata_entry_service.repository.list_metadata_summary.return_value = []

        metadata_entry_service.list_metadata(mock_db_session, limit=50)

        metadata_entry_service.repository.list_metadata_summary.assert_called_once_with(mock_db_session, limit=50)

    def test_list_metadata_no_limit(self, metadata_entry_service, mock_db_session):
        """Should work without limit."""
        metadata_entry_service.repository.list_metadata_summary.return_value = []

        metadata_entry_service.list_metadata(mock_db_session)

        metadata_entry_service.repository.list_metadata_summary.assert_called_once_with(mock_db_session, limit=None)

    # ========================================================================
    # search_metadata tests
    # ========================================================================

    def test_search_metadata_with_query(self, metadata_entry_service, mock_db_session):
        """Should search with query parameter."""
        mock_entry = MagicMock()
        mock_entry.model_dump.return_value = {
            "metadata_id": "test-id",
            "metadata_schema": "name",
            "value": "Test",
            "ingested_at": datetime(2024, 1, 1),
        }
        metadata_entry_service.repository.search_metadata.return_value = [mock_entry]

        result = metadata_entry_service.search_metadata(mock_db_session, query="test")

        assert len(result) == 1
        assert result[0]["ingested_at"] == "2024-01-01 00:00:00"

    def test_search_metadata_with_schema_filter(self, metadata_entry_service, mock_db_session):
        """Should search with schema filter."""
        metadata_entry_service.repository.search_metadata.return_value = []

        metadata_entry_service.search_metadata(mock_db_session, schema="name")

        metadata_entry_service.repository.search_metadata.assert_called_once_with(
            db=mock_db_session, query=None, schema="name", metadata_id=None
        )

    def test_search_metadata_with_metadata_id_filter(self, metadata_entry_service, mock_db_session):
        """Should search with metadata_id filter."""
        metadata_entry_service.repository.search_metadata.return_value = []

        metadata_entry_service.search_metadata(mock_db_session, metadata_id="specific-id")

        metadata_entry_service.repository.search_metadata.assert_called_once_with(
            db=mock_db_session, query=None, schema=None, metadata_id="specific-id"
        )

    # ========================================================================
    # get_all_metadata_schemas tests
    # ========================================================================

    def test_get_all_metadata_schemas(self, metadata_entry_service, mock_db_session):
        """Should return all unique schemas from DB."""
        expected_schemas = ["name", "description", "keywords", "dateModified"]
        metadata_entry_service.repository.get_all_distinct_metadata_schemas.return_value = expected_schemas

        result = metadata_entry_service.get_all_metadata_schemas(mock_db_session)

        assert result == expected_schemas
        metadata_entry_service.repository.get_all_distinct_metadata_schemas.assert_called_once_with(mock_db_session)
