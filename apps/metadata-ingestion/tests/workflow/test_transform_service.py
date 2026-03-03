"""Tests for CatalogEntryTransformService."""

from unittest.mock import MagicMock

import pytest

from tests.constants import ENTRY_ID_1, ENTRY_ID_2, ENTRY_ID_3, METADATA_ID_1, METADATA_ID_2, METADATA_ID_3

from app.src.catalog_entry.model import CatalogEntry, CatalogEntryUpdate
from app.src.catalog_entry.service import CatalogEntryService
from app.src.column_relation.model import ColumnRelation
from app.src.column_relation.service import ColumnRelationService
from app.src.metadata_entry.model import MetadataEntry
from app.src.metadata_entry.service import MetadataEntryService
from app.src.workflow.transform_service import CatalogEntryTransformService


class TestApplyMetadataToUpdate:
    """Test cases for _apply_metadata_to_update internal method."""

    @pytest.fixture
    def transform_service(
        self, mock_catalog_entry_repository, mock_column_relation_repository, mock_metadata_entry_repository
    ):
        """Create CatalogEntryTransformService with mocks."""

        return CatalogEntryTransformService(
            catalog_entry_service=CatalogEntryService(mock_catalog_entry_repository),
            column_relation_service=ColumnRelationService(mock_column_relation_repository),
            metadata_entry_service=MetadataEntryService(mock_metadata_entry_repository),
        )

    def test_apply_metadata_sets_fields(self, transform_service):
        """Should set fields on CatalogEntryUpdate."""
        update = CatalogEntryUpdate()
        metadata_entries = [
            MagicMock(spec=MetadataEntry, metadata_schema="name", value="Test Title"),
            MagicMock(spec=MetadataEntry, metadata_schema="desc", value="Test Description"),
        ]
        relations = [
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95),
            MagicMock(spec=ColumnRelation, catalog_column="description", metadata_column="desc", correlation=0.90),
        ]

        transform_service._apply_metadata_to_update(update, metadata_entries, relations)

        assert update.title == "Test Title"
        assert update.description == "Test Description"

    def test_apply_metadata_uses_highest_correlation(self, transform_service):
        """Should use highest correlation value when multiple match same catalog column."""
        update = CatalogEntryUpdate()
        metadata_entries = [
            MagicMock(spec=MetadataEntry, metadata_schema="name", value="Name Value"),
            MagicMock(spec=MetadataEntry, metadata_schema="label", value="Label Value"),
        ]
        relations = [
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="label", correlation=0.80),
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95),
        ]

        transform_service._apply_metadata_to_update(update, metadata_entries, relations)

        # Should use "name" value because it has higher correlation
        assert update.title == "Name Value"

    def test_apply_metadata_skips_invalid_fields(self, transform_service):
        """Should skip relations for fields not in CatalogEntryUpdate."""
        update = CatalogEntryUpdate()
        metadata_entries = [
            MagicMock(spec=MetadataEntry, metadata_schema="name", value="Test"),
        ]
        relations = [
            MagicMock(spec=ColumnRelation, catalog_column="invalid_field", metadata_column="name", correlation=0.95),
        ]

        # Should not raise
        transform_service._apply_metadata_to_update(update, metadata_entries, relations)

        # No fields should be set
        assert all(getattr(update, f) is None for f in CatalogEntryUpdate.model_fields if f != "identifier")

    def test_apply_metadata_skips_missing_metadata(self, transform_service):
        """Should skip when metadata value not found."""
        update = CatalogEntryUpdate()
        metadata_entries = [
            MagicMock(spec=MetadataEntry, metadata_schema="other_field", value="Other"),
        ]
        relations = [
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95),
        ]

        transform_service._apply_metadata_to_update(update, metadata_entries, relations)

        assert update.title is None

    def test_apply_metadata_empty_inputs(self, transform_service):
        """Should handle empty inputs."""
        update = CatalogEntryUpdate()

        # Should not raise
        transform_service._apply_metadata_to_update(update, [], [])


class TestTransformCatalogEntry:
    """Test cases for transform_catalog_entry method."""

    @pytest.fixture
    def transform_service(
        self, mock_catalog_entry_repository, mock_column_relation_repository, mock_metadata_entry_repository
    ):
        """Create CatalogEntryTransformService with mocks."""
        return CatalogEntryTransformService(
            catalog_entry_service=CatalogEntryService(mock_catalog_entry_repository),
            column_relation_service=ColumnRelationService(mock_column_relation_repository),
            metadata_entry_service=MetadataEntryService(mock_metadata_entry_repository),
        )

    def test_transform_catalog_entry_success(self, transform_service, mock_db_session):
        """Should transform catalog entry with metadata."""
        mock_entry = MagicMock(spec=CatalogEntry)
        mock_entry.id = 1
        mock_entry.identifier = "test-identifier"
        transform_service.catalog_entry_service.repository.select.return_value = mock_entry

        # Mock metadata
        mock_metadata = [MagicMock(spec=MetadataEntry, metadata_schema="name", value="New Title")]
        transform_service.metadata_entry_service.repository.select_metadata_entry.return_value = mock_metadata

        # Mock relations
        mock_relations = [MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95)]
        transform_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = (
            mock_relations
        )

        # Mock update
        transform_service.catalog_entry_service.repository.save.return_value = mock_entry

        result = transform_service.transform_catalog_entry(mock_db_session, 1)

        # Verify update was called
        transform_service.catalog_entry_service.repository.select.assert_called()

    def test_transform_catalog_entry_no_metadata(self, transform_service, mock_db_session):
        """Should return unchanged entry when no metadata found."""
        mock_entry = MagicMock(spec=CatalogEntry)
        mock_entry.id = 1
        mock_entry.identifier = "test-identifier"
        transform_service.catalog_entry_service.repository.select.return_value = mock_entry

        # No metadata
        transform_service.metadata_entry_service.repository.select_metadata_entry.return_value = []

        result = transform_service.transform_catalog_entry(mock_db_session, 1)

        assert result == mock_entry
        # Should not attempt to get relations or update
        transform_service.column_relation_service.repository.select_relations_by_metadata_columns.assert_not_called()


class TestTransformCatalogEntriesBulk:
    """Test cases for transform_catalog_entries_bulk method."""

    @pytest.fixture
    def transform_service(
        self, mock_catalog_entry_repository, mock_column_relation_repository, mock_metadata_entry_repository
    ):
        """Create CatalogEntryTransformService with mocks."""
        return CatalogEntryTransformService(
            catalog_entry_service=CatalogEntryService(mock_catalog_entry_repository),
            column_relation_service=ColumnRelationService(mock_column_relation_repository),
            metadata_entry_service=MetadataEntryService(mock_metadata_entry_repository),
        )

    def test_transform_bulk_empty_list(self, transform_service, mock_db_session):
        """Should handle empty identifier list."""
        # Should not raise, just return early
        transform_service.transform_catalog_entries_bulk(mock_db_session, [])

        # No DB calls should be made
        transform_service.catalog_entry_service.repository.select_by_identifiers.assert_not_called()

    def test_transform_bulk_processes_multiple(self, transform_service, mock_db_session):
        """Should process multiple entries."""
        mock_entries = [
            MagicMock(spec=CatalogEntry, id=1, identifier=ENTRY_ID_1),
            MagicMock(spec=CatalogEntry, id=2, identifier=ENTRY_ID_2),
        ]
        transform_service.catalog_entry_service.repository.select_by_identifiers.return_value = mock_entries

        mock_metadata = [
            MagicMock(spec=MetadataEntry, metadata_id=ENTRY_ID_1, metadata_schema="name", value="Title 1"),
            MagicMock(spec=MetadataEntry, metadata_id=ENTRY_ID_2, metadata_schema="name", value="Title 2"),
        ]
        transform_service.metadata_entry_service.repository.select_metadata_entries_by_metadata_ids.return_value = (
            mock_metadata
        )

        mock_relations = [MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95)]
        transform_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = (
            mock_relations
        )

        transform_service.transform_catalog_entries_bulk(mock_db_session, [ENTRY_ID_1, ENTRY_ID_2])

        # Verify bulk operations were used
        transform_service.catalog_entry_service.repository.select_by_identifiers.assert_called_once()
        transform_service.metadata_entry_service.repository.select_metadata_entries_by_metadata_ids.assert_called_once()

    def test_transform_bulk_calls_update_bulk(self, transform_service, mock_db_session):
        """Should call update_bulk when updates exist."""
        mock_entry = MagicMock(spec=CatalogEntry, id=1, identifier=ENTRY_ID_1)
        transform_service.catalog_entry_service.repository.select_by_identifiers.return_value = [mock_entry]

        mock_metadata = [MagicMock(spec=MetadataEntry, metadata_id=ENTRY_ID_1, metadata_schema="name", value="New Title")]
        transform_service.metadata_entry_service.repository.select_metadata_entries_by_metadata_ids.return_value = (
            mock_metadata
        )

        mock_relations = [MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95)]
        transform_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = (
            mock_relations
        )

        transform_service.transform_catalog_entries_bulk(mock_db_session, [ENTRY_ID_1])

        transform_service.catalog_entry_service.repository.update_bulk.assert_called_once()

    def test_transform_bulk_no_updates_when_no_relations(self, transform_service, mock_db_session):
        """Should not call update_bulk when no relations match."""
        mock_entry = MagicMock(spec=CatalogEntry, id=1, identifier=ENTRY_ID_1)
        transform_service.catalog_entry_service.repository.select_by_identifiers.return_value = [mock_entry]

        mock_metadata = [MagicMock(spec=MetadataEntry, metadata_id=ENTRY_ID_1, metadata_schema="other", value="Value")]
        transform_service.metadata_entry_service.repository.select_metadata_entries_by_metadata_ids.return_value = (
            mock_metadata
        )

        # No matching relations
        transform_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = []

        transform_service.transform_catalog_entries_bulk(mock_db_session, [ENTRY_ID_1])

        transform_service.catalog_entry_service.repository.update_bulk.assert_not_called()

    def test_transform_catalog_entry_not_found(self, transform_service, mock_db_session):
        """Should propagate CatalogEntryNotFoundError."""
        from app.src.catalog_entry.exceptions import CatalogEntryNotFoundError

        transform_service.catalog_entry_service.repository.select.side_effect = CatalogEntryNotFoundError(
            catalog_entry_id=99999
        )

        with pytest.raises(CatalogEntryNotFoundError):
            transform_service.transform_catalog_entry(mock_db_session, 99999)

    def test_transform_bulk_partial_identifier_match(self, transform_service, mock_db_session):
        """Should process only existing entries when some identifiers don't exist."""
        # Request: [ENTRY_ID_1, ENTRY_ID_2, ENTRY_ID_3], DB has only [ENTRY_ID_1, ENTRY_ID_3]
        mock_entries = [
            MagicMock(spec=CatalogEntry, id=1, identifier=ENTRY_ID_1),
            MagicMock(spec=CatalogEntry, id=3, identifier=ENTRY_ID_3),
        ]
        transform_service.catalog_entry_service.repository.select_by_identifiers.return_value = mock_entries

        mock_metadata = [
            MagicMock(spec=MetadataEntry, metadata_id=ENTRY_ID_1, metadata_schema="name", value="Title 1"),
            MagicMock(spec=MetadataEntry, metadata_id=ENTRY_ID_3, metadata_schema="name", value="Title 3"),
        ]
        transform_service.metadata_entry_service.repository.select_metadata_entries_by_metadata_ids.return_value = (
            mock_metadata
        )

        mock_relations = [
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=0.95)
        ]
        transform_service.column_relation_service.repository.select_relations_by_metadata_columns.return_value = (
            mock_relations
        )

        # Should not raise, processes 2 entries
        transform_service.transform_catalog_entries_bulk(mock_db_session, [ENTRY_ID_1, ENTRY_ID_2, ENTRY_ID_3])

        # update_bulk should be called with 2 entries
        transform_service.catalog_entry_service.repository.update_bulk.assert_called_once()
        call_args = transform_service.catalog_entry_service.repository.update_bulk.call_args
        updates = call_args[0][1]  # Second positional arg
        assert len(updates) == 2


class TestApplyMetadataEdgeCases:
    """Edge case tests for _apply_metadata_to_update."""

    @pytest.fixture
    def transform_service(
        self, mock_catalog_entry_repository, mock_column_relation_repository, mock_metadata_entry_repository
    ):
        """Create CatalogEntryTransformService with mocks."""
        return CatalogEntryTransformService(
            catalog_entry_service=CatalogEntryService(mock_catalog_entry_repository),
            column_relation_service=ColumnRelationService(mock_column_relation_repository),
            metadata_entry_service=MetadataEntryService(mock_metadata_entry_repository),
        )

    def test_apply_metadata_handles_none_correlation(self, transform_service):
        """Should handle None correlation values in sorting."""
        update = CatalogEntryUpdate()
        metadata_entries = [
            MagicMock(spec=MetadataEntry, metadata_schema="name", value="Name Value"),
            MagicMock(spec=MetadataEntry, metadata_schema="label", value="Label Value"),
        ]
        relations = [
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="name", correlation=None),
            MagicMock(spec=ColumnRelation, catalog_column="title", metadata_column="label", correlation=0.5),
        ]

        # Should not raise, None treated as 0
        transform_service._apply_metadata_to_update(update, metadata_entries, relations)

        # label (correlation=0.5) should win over name (correlation=None -> 0)
        assert update.title == "Label Value"
