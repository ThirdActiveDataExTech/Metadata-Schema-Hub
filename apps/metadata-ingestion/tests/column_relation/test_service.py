"""Tests for ColumnRelationService."""

from unittest.mock import MagicMock

from active_metadata.models import ColumnRelationBase
from app.src.column_relation.model import ColumnRelation


class TestColumnRelationService:
    """Test cases for ColumnRelationService."""

    # ========================================================================
    # create_single_relation tests
    # ========================================================================

    def test_create_single_relation(self, column_relation_service, mock_db_session):
        """Should create single column relation."""
        relation_base = ColumnRelationBase(catalog_column="title", metadata_column="name", correlation=0.95)

        # Mock repository to return what was passed
        column_relation_service.repository.save.side_effect = lambda db, r: r

        result = column_relation_service.create_single_relation(mock_db_session, relation_base)

        assert isinstance(result, ColumnRelation)
        assert result.catalog_column == "title"
        assert result.metadata_column == "name"
        assert result.correlation == 0.95
        column_relation_service.repository.save.assert_called_once()

    # ========================================================================
    # create_relations tests
    # ========================================================================

    def test_create_relations_multiple(self, column_relation_service, mock_db_session):
        """Should create multiple relations."""
        relations = [
            ColumnRelationBase(catalog_column="title", metadata_column="name", correlation=0.95),
            ColumnRelationBase(catalog_column="description", metadata_column="desc", correlation=0.90),
            ColumnRelationBase(catalog_column="keyword", metadata_column="keywords", correlation=0.85),
        ]

        column_relation_service.repository.save_bulk.side_effect = lambda db, r: r

        result = column_relation_service.create_relations(mock_db_session, relations)

        assert len(result) == 3
        assert all(isinstance(r, ColumnRelation) for r in result)
        column_relation_service.repository.save_bulk.assert_called_once()

    def test_create_relations_empty_list(self, column_relation_service, mock_db_session):
        """Should handle empty list."""
        column_relation_service.repository.save_bulk.return_value = []

        result = column_relation_service.create_relations(mock_db_session, [])

        assert result == []
        column_relation_service.repository.save_bulk.assert_called_once()

    # ========================================================================
    # get_relations_by_catalog_column tests
    # ========================================================================

    def test_get_relations_by_catalog_column(self, column_relation_service, mock_db_session):
        """Should return relations for catalog column."""
        expected = [
            MagicMock(catalog_column="title", metadata_column="name", correlation=0.95),
            MagicMock(catalog_column="title", metadata_column="title", correlation=0.90),
        ]
        column_relation_service.repository.select_relations_by_catalog_column.return_value = expected

        result = column_relation_service.get_relations_by_catalog_column(mock_db_session, "title")

        assert result == expected
        column_relation_service.repository.select_relations_by_catalog_column.assert_called_once_with(
            mock_db_session, "title"
        )

    def test_get_relations_by_catalog_column_not_found(self, column_relation_service, mock_db_session):
        """Should return empty list when no relations found."""
        column_relation_service.repository.select_relations_by_catalog_column.return_value = []

        result = column_relation_service.get_relations_by_catalog_column(mock_db_session, "nonexistent")

        assert result == []

    # ========================================================================
    # get_relations_by_metadata_column tests
    # ========================================================================

    def test_get_relations_by_metadata_column(self, column_relation_service, mock_db_session):
        """Should return relations for metadata column."""
        expected = [MagicMock(catalog_column="title", metadata_column="name", correlation=0.95)]
        column_relation_service.repository.select_relations_by_metadata_column.return_value = expected

        result = column_relation_service.get_relations_by_metadata_column(mock_db_session, "name")

        assert result == expected
        column_relation_service.repository.select_relations_by_metadata_column.assert_called_once_with(
            mock_db_session, "name"
        )

    # ========================================================================
    # get_relations_by_metadata_columns tests
    # ========================================================================

    def test_get_relations_by_metadata_columns(self, column_relation_service, mock_db_session):
        """Should return relations for multiple metadata columns."""
        expected = [
            MagicMock(catalog_column="title", metadata_column="name", correlation=0.95),
            MagicMock(catalog_column="description", metadata_column="desc", correlation=0.90),
        ]
        column_relation_service.repository.select_relations_by_metadata_columns.return_value = expected

        result = column_relation_service.get_relations_by_metadata_columns(mock_db_session, ["name", "desc"])

        assert result == expected
        column_relation_service.repository.select_relations_by_metadata_columns.assert_called_once_with(
            mock_db_session, ["name", "desc"]
        )

    def test_get_relations_by_metadata_columns_empty_list(self, column_relation_service, mock_db_session):
        """Should handle empty list."""
        column_relation_service.repository.select_relations_by_metadata_columns.return_value = []

        result = column_relation_service.get_relations_by_metadata_columns(mock_db_session, [])

        assert result == []

    # ========================================================================
    # get_all_relations tests
    # ========================================================================

    def test_get_all_relations(self, column_relation_service, mock_db_session):
        """Should return all relations."""
        expected = [MagicMock(), MagicMock(), MagicMock()]
        column_relation_service.repository.select_all_relations.return_value = expected

        result = column_relation_service.get_all_relations(mock_db_session)

        assert result == expected
        column_relation_service.repository.select_all_relations.assert_called_once_with(mock_db_session)

    # ========================================================================
    # replace_catalog_relations tests
    # ========================================================================

    def test_replace_catalog_relations(self, column_relation_service, mock_db_session):
        """Should delete existing and create new relations."""
        new_predictions = [("name", 0.95), ("title", 0.90), ("label", 0.85)]

        column_relation_service.repository.delete_relations_by_catalog_column.return_value = 2
        column_relation_service.repository.save_bulk.side_effect = lambda db, r: r

        result = column_relation_service.replace_catalog_relations(mock_db_session, "title", new_predictions)

        # Verify delete was called
        column_relation_service.repository.delete_relations_by_catalog_column.assert_called_once_with(
            mock_db_session, "title"
        )

        # Verify save_bulk was called with new relations
        column_relation_service.repository.save_bulk.assert_called_once()
        saved_relations = column_relation_service.repository.save_bulk.call_args[0][1]
        assert len(saved_relations) == 3
        assert all(r.catalog_column == "title" for r in saved_relations)

    def test_replace_catalog_relations_empty_predictions(self, column_relation_service, mock_db_session):
        """Should handle empty predictions (delete only)."""
        column_relation_service.repository.delete_relations_by_catalog_column.return_value = 2
        column_relation_service.repository.save_bulk.return_value = []

        result = column_relation_service.replace_catalog_relations(mock_db_session, "title", [])

        column_relation_service.repository.delete_relations_by_catalog_column.assert_called_once()
        column_relation_service.repository.save_bulk.assert_called_once()
        assert result == []

    def test_replace_catalog_relations_creates_correct_objects(self, column_relation_service, mock_db_session):
        """Should create ColumnRelation objects with correct values."""
        new_predictions = [("meta_name", 0.95), ("meta_title", 0.85)]

        column_relation_service.repository.save_bulk.side_effect = lambda db, r: r

        result = column_relation_service.replace_catalog_relations(mock_db_session, "catalog_title", new_predictions)

        assert len(result) == 2
        assert result[0].catalog_column == "catalog_title"
        assert result[0].metadata_column == "meta_name"
        assert result[0].correlation == 0.95
        assert result[1].metadata_column == "meta_title"
        assert result[1].correlation == 0.85
