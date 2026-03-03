"""Tests for MetadataEntryService."""

from unittest.mock import MagicMock


from app.src.metadata_entry.model import MetadataEntry
from app.src.metadata_entry.service import MetadataEntryService


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

        result = metadata_entry_service.select_metadata(mock_db, "meta-123")

        assert result == entries
        mock_metadata_entry_repository.select_metadata_entry.assert_called_once_with(mock_db, "meta-123")


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

        result = metadata_entry_service.select_metadata_schemas_distinct(mock_db, ["meta-1", "meta-2"])

        assert result == schemas
        mock_metadata_entry_repository.select_distinct_metadata_schemas.assert_called_once_with(
            mock_db, ["meta-1", "meta-2"]
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

        result = metadata_entry_service.select_metadata_bulk(mock_db, ["meta-1", "meta-2"])

        assert result == entries
        mock_metadata_entry_repository.select_metadata_entries_by_metadata_ids.assert_called_once_with(
            mock_db, ["meta-1", "meta-2"]
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
        sample_metadata_entry: MetadataEntry,
    ) -> None:
        """Should search with text query."""
        mock_metadata_entry_repository.search_metadata.return_value = [sample_metadata_entry]

        result = metadata_entry_service.search_metadata(mock_db, query="sample")

        assert len(result) == 1
        assert result[0]["metadata_schema"] == "dct:title"
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

        result = metadata_entry_service.search_metadata(mock_db, schema="dct:title")

        mock_metadata_entry_repository.search_metadata.assert_called_once_with(
            db=mock_db, query=None, schema="dct:title", metadata_id=None
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

        result = metadata_entry_service.search_metadata(mock_db, metadata_id="meta-123")

        mock_metadata_entry_repository.search_metadata.assert_called_once_with(
            db=mock_db, query=None, schema=None, metadata_id="meta-123"
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
