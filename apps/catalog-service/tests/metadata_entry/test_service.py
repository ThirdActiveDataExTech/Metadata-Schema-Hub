"""Tests for MetadataEntryService."""

from datetime import datetime
from unittest.mock import MagicMock

from app.src.metadata_entry.model import MetadataEntry
from app.src.metadata_entry.service import MetadataEntryService
from tests.constants import METADATA_ID_1, METADATA_ID_2


class TestSelectMetadata:
    """Tests for select_metadata method."""

    def test_returns_metadata_entries(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_metadata_entry: MetadataEntry,
    ) -> None:
        """Should return metadata entries for given metadata_id."""
        entries = [sample_metadata_entry]
        mock_metadata_entry_repository.select_metadata_entry.return_value = entries

        result = metadata_entry_service.select_metadata(mock_db, METADATA_ID_1)

        assert result == entries
        mock_metadata_entry_repository.select_metadata_entry.assert_called_once_with(mock_db, METADATA_ID_1)


class TestSelectMetadataSchemasDistinct:
    """Tests for select_metadata_schemas_distinct method."""

    def test_returns_distinct_schemas(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return distinct metadata schemas."""
        schemas = ["dct:title", "dct:description", "dcat:keyword"]
        mock_metadata_entry_repository.select_distinct_metadata_schemas.return_value = schemas

        result = metadata_entry_service.select_metadata_schemas_distinct(mock_db, [METADATA_ID_1, METADATA_ID_2])

        assert result == schemas
        mock_metadata_entry_repository.select_distinct_metadata_schemas.assert_called_once_with(
            mock_db, [METADATA_ID_1, METADATA_ID_2]
        )


class TestSelectMetadataBulk:
    """Tests for select_metadata_bulk method."""

    def test_returns_entries_for_multiple_ids(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_metadata_entry: MetadataEntry,
    ) -> None:
        """Should return entries for multiple metadata IDs."""
        entries = [sample_metadata_entry]
        mock_metadata_entry_repository.select_metadata_entries_by_metadata_ids.return_value = entries

        result = metadata_entry_service.select_metadata_bulk(mock_db, [METADATA_ID_1, METADATA_ID_2])

        assert result == entries
        mock_metadata_entry_repository.select_metadata_entries_by_metadata_ids.assert_called_once_with(
            mock_db, [METADATA_ID_1, METADATA_ID_2]
        )


class TestListMetadata:
    """Tests for list_metadata method."""

    def test_returns_metadata_list(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_metadata_entry: MetadataEntry,
    ) -> None:
        """Should return list of metadata entries."""
        entries = [sample_metadata_entry]
        mock_metadata_entry_repository.list_metadata_summary.return_value = entries

        result = metadata_entry_service.list_metadata(mock_db)

        assert result == entries
        mock_metadata_entry_repository.list_metadata_summary.assert_called_once_with(mock_db, limit=None)

    def test_passes_limit_parameter(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should pass limit parameter to repository."""
        mock_metadata_entry_repository.list_metadata_summary.return_value = []

        metadata_entry_service.list_metadata(mock_db, limit=50)

        mock_metadata_entry_repository.list_metadata_summary.assert_called_once_with(mock_db, limit=50)

    def test_passes_negative_limit_to_repository(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should pass negative limit to repository (validation at DB/repository level)."""
        mock_metadata_entry_repository.list_metadata_summary.return_value = []

        metadata_entry_service.list_metadata(mock_db, limit=-1)

        # Service passes through; repository/DB handles validation
        mock_metadata_entry_repository.list_metadata_summary.assert_called_once_with(mock_db, limit=-1)


class TestSearchMetadata:
    """Tests for search_metadata method."""

    def test_search_with_query(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should search with text query."""

        entry = MetadataEntry(
            id=1,
            metadata_schema="dct:title",
            value="Test Value",
            metadata_id=METADATA_ID_1,
            ingested_at=datetime(2024, 1, 1),
        )
        mock_metadata_entry_repository.search_metadata.return_value = [entry]

        result = metadata_entry_service.search_metadata(mock_db, query="sample")

        assert len(result) == 1
        assert result[0]["metadata_schema"] == entry.metadata_schema
        mock_metadata_entry_repository.search_metadata.assert_called_once_with(
            db=mock_db, query="sample", schema=None, metadata_id=None
        )

    def test_search_with_schema_filter(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_metadata_entry: MetadataEntry,
    ) -> None:
        """Should search with schema filter."""
        mock_metadata_entry_repository.search_metadata.return_value = [sample_metadata_entry]

        search_schema = "dct:title"

        result = metadata_entry_service.search_metadata(mock_db, schema=search_schema)

        mock_metadata_entry_repository.search_metadata.assert_called_once_with(
            db=mock_db, query=None, schema=search_schema, metadata_id=None
        )

    def test_search_with_metadata_id_filter(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_metadata_entry: MetadataEntry,
    ) -> None:
        """Should search with metadata_id filter."""
        mock_metadata_entry_repository.search_metadata.return_value = [sample_metadata_entry]

        result = metadata_entry_service.search_metadata(mock_db, metadata_id=METADATA_ID_1)

        mock_metadata_entry_repository.search_metadata.assert_called_once_with(
            db=mock_db, query=None, schema=None, metadata_id=METADATA_ID_1
        )

    def test_converts_ingested_at_to_string(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
        sample_metadata_entry: MetadataEntry,
    ) -> None:
        """Should convert ingested_at datetime to string."""
        mock_metadata_entry_repository.search_metadata.return_value = [sample_metadata_entry]

        result = metadata_entry_service.search_metadata(mock_db)

        assert isinstance(result[0]["ingested_at"], str)

    def test_search_returns_empty_list(
        self,
        metadata_entry_service: MetadataEntryService,
        mock_metadata_entry_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return empty list when no matches found."""
        mock_metadata_entry_repository.search_metadata.return_value = []

        result = metadata_entry_service.search_metadata(mock_db, query="nonexistent")

        assert result == []
