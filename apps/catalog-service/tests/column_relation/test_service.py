"""Tests for ColumnRelationService."""

from unittest.mock import MagicMock

from app.src.column_relation.model import ColumnRelation
from app.src.column_relation.service import ColumnRelationService


class TestGetRelationsByCatalogColumn:
    """Tests for get_relations_by_catalog_column method."""

    def test_returns_relations_by_catalog_column(
        self,
        column_relation_service: ColumnRelationService,
        mock_column_relation_repository: MagicMock,
        mock_db: MagicMock,
        sample_column_relation: ColumnRelation,
    ) -> None:
        """Should return relations for given catalog column."""
        relations = [sample_column_relation]
        mock_column_relation_repository.select_relations_by_catalog_column.return_value = relations

        result = column_relation_service.get_relations_by_catalog_column(mock_db, "title")

        assert result == relations
        mock_column_relation_repository.select_relations_by_catalog_column.assert_called_once_with(
            mock_db, "title"
        )

    def test_returns_empty_list_for_unknown_column(
        self,
        column_relation_service: ColumnRelationService,
        mock_column_relation_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return empty list for unknown column."""
        mock_column_relation_repository.select_relations_by_catalog_column.return_value = []

        result = column_relation_service.get_relations_by_catalog_column(mock_db, "unknown")

        assert result == []

    def test_handles_empty_string_column(
        self,
        column_relation_service: ColumnRelationService,
        mock_column_relation_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should handle empty string column name (passes through to repository)."""
        mock_column_relation_repository.select_relations_by_catalog_column.return_value = []

        result = column_relation_service.get_relations_by_catalog_column(mock_db, "")

        assert result == []
        mock_column_relation_repository.select_relations_by_catalog_column.assert_called_once_with(
            mock_db, ""
        )


class TestGetRelationsByMetadataColumn:
    """Tests for get_relations_by_metadata_column method."""

    def test_returns_relations_by_metadata_column(
        self,
        column_relation_service: ColumnRelationService,
        mock_column_relation_repository: MagicMock,
        mock_db: MagicMock,
        sample_column_relation: ColumnRelation,
    ) -> None:
        """Should return relations for given metadata column."""
        relations = [sample_column_relation]
        mock_column_relation_repository.select_relations_by_metadata_column.return_value = relations

        result = column_relation_service.get_relations_by_metadata_column(mock_db, "dct:title")

        assert result == relations
        mock_column_relation_repository.select_relations_by_metadata_column.assert_called_once_with(
            mock_db, "dct:title"
        )


class TestGetRelationsByMetadataColumns:
    """Tests for get_relations_by_metadata_columns method."""

    def test_returns_relations_for_multiple_columns(
        self,
        column_relation_service: ColumnRelationService,
        mock_column_relation_repository: MagicMock,
        mock_db: MagicMock,
        sample_column_relation: ColumnRelation,
    ) -> None:
        """Should return relations for multiple metadata columns."""
        relation1 = sample_column_relation
        relation2 = ColumnRelation(
            id=2,
            catalog_column="description",
            metadata_column="dct:description",
            correlation=0.90,
        )
        relations = [relation1, relation2]
        mock_column_relation_repository.select_relations_by_metadata_columns.return_value = relations

        result = column_relation_service.get_relations_by_metadata_columns(
            mock_db, ["dct:title", "dct:description"]
        )

        assert result == relations
        assert len(result) == 2
        mock_column_relation_repository.select_relations_by_metadata_columns.assert_called_once_with(
            mock_db, ["dct:title", "dct:description"]
        )

    def test_returns_empty_list_for_empty_input(
        self,
        column_relation_service: ColumnRelationService,
        mock_column_relation_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return empty list for empty input."""
        mock_column_relation_repository.select_relations_by_metadata_columns.return_value = []

        result = column_relation_service.get_relations_by_metadata_columns(mock_db, [])

        assert result == []

    def test_handles_duplicate_columns_in_list(
        self,
        column_relation_service: ColumnRelationService,
        mock_column_relation_repository: MagicMock,
        mock_db: MagicMock,
        sample_column_relation: ColumnRelation,
    ) -> None:
        """Should pass duplicate column names to repository (no dedup at service)."""
        mock_column_relation_repository.select_relations_by_metadata_columns.return_value = [
            sample_column_relation
        ]

        result = column_relation_service.get_relations_by_metadata_columns(
            mock_db, ["dct:title", "dct:title", "dct:title"]
        )

        # Service passes through duplicates; repository/DB handles dedup
        mock_column_relation_repository.select_relations_by_metadata_columns.assert_called_once_with(
            mock_db, ["dct:title", "dct:title", "dct:title"]
        )
        assert len(result) == 1


class TestGetAllRelations:
    """Tests for get_all_relations method."""

    def test_returns_all_relations(
        self,
        column_relation_service: ColumnRelationService,
        mock_column_relation_repository: MagicMock,
        mock_db: MagicMock,
        sample_column_relation: ColumnRelation,
    ) -> None:
        """Should return all column relations."""
        relations = [
            sample_column_relation,
            ColumnRelation(id=2, catalog_column="description", metadata_column="dct:description", correlation=0.85),
            ColumnRelation(id=3, catalog_column="keyword", metadata_column="dcat:keyword", correlation=0.92),
        ]
        mock_column_relation_repository.select_all_relations.return_value = relations

        result = column_relation_service.get_all_relations(mock_db)

        assert result == relations
        assert len(result) == 3
        mock_column_relation_repository.select_all_relations.assert_called_once_with(mock_db)

    def test_returns_empty_list_when_no_relations(
        self,
        column_relation_service: ColumnRelationService,
        mock_column_relation_repository: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Should return empty list when no relations exist."""
        mock_column_relation_repository.select_all_relations.return_value = []

        result = column_relation_service.get_all_relations(mock_db)

        assert result == []
