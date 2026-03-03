"""Integration tests for ColumnRelationRepository."""

import pytest
from sqlmodel import Session

from app.src.column_relation.model import ColumnRelation
from app.src.column_relation.repository import ColumnRelationRepository


class TestSave:
    """Tests for save method."""

    def test_save_relation(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
    ) -> None:
        """Should save relation and return with ID."""
        relation = ColumnRelation(
            catalog_column="test_col",
            metadata_column="dct:test",
            correlation=0.75,
        )

        result = column_relation_repository.save(db, relation)

        assert result.id is not None
        assert result.catalog_column == "test_col"


class TestSaveBulk:
    """Tests for save_bulk method."""

    def test_save_multiple_relations(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
    ) -> None:
        """Should save multiple relations."""
        relations = [
            ColumnRelation(
                catalog_column="col1",
                metadata_column="dct:col1",
                correlation=0.90,
            ),
            ColumnRelation(
                catalog_column="col2",
                metadata_column="dct:col2",
                correlation=0.85,
            ),
        ]

        result = column_relation_repository.save_bulk(db, relations)

        assert len(result) == 2
        assert all(r.id is not None for r in result)


class TestSelectRelationsByCatalogColumn:
    """Tests for select_relations_by_catalog_column method."""

    def test_select_by_catalog_column(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
    ) -> None:
        """Should return relations for catalog column."""
        target_column = "title"
        result = column_relation_repository.select_relations_by_catalog_column(
            db, target_column
        )
        expected_count = sum(
            1 for r in sample_column_relations if r.catalog_column == target_column
        )
        assert len(result) == expected_count
        # Ordered by correlation desc
        assert result[0].correlation >= result[1].correlation

    def test_select_nonexistent(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
    ) -> None:
        """Should return empty list."""
        result = column_relation_repository.select_relations_by_catalog_column(
            db, "nonexistent"
        )
        assert result == []


class TestSelectRelationsByMetadataColumn:
    """Tests for select_relations_by_metadata_column method."""

    def test_select_by_metadata_column(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
    ) -> None:
        """Should return relations for metadata column."""
        target_column = "dct:title"
        result = column_relation_repository.select_relations_by_metadata_column(
            db, target_column
        )
        expected = [r for r in sample_column_relations if r.metadata_column == target_column]
        assert len(result) == len(expected)
        assert result[0].catalog_column == expected[0].catalog_column


class TestSelectRelationsByThreshold:
    """Tests for select_relations_by_threshold method."""

    def test_select_above_threshold(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
    ) -> None:
        """Should return relations above threshold."""
        threshold = 0.90
        result = column_relation_repository.select_relations_by_threshold(db, threshold)
        expected_count = sum(
            1 for r in sample_column_relations if r.correlation >= threshold
        )
        assert len(result) == expected_count
        assert all(r.correlation >= threshold for r in result)


class TestSelectAllRelations:
    """Tests for select_all_relations method."""

    def test_select_all(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
    ) -> None:
        """Should return all relations."""
        result = column_relation_repository.select_all_relations(db)
        assert len(result) == len(sample_column_relations)


class TestDeleteRelationsByCatalogColumn:
    """Tests for delete_relations_by_catalog_column method."""

    def test_delete_by_catalog_column(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
    ) -> None:
        """Should delete relations and return count."""
        target_column = "title"
        expected_delete_count = sum(
            1 for r in sample_column_relations if r.catalog_column == target_column
        )
        count = column_relation_repository.delete_relations_by_catalog_column(
            db, target_column
        )

        assert count == expected_delete_count

        # Verify deletion
        result = column_relation_repository.select_relations_by_catalog_column(
            db, target_column
        )
        assert result == []

    def test_delete_nonexistent(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
    ) -> None:
        """Should return 0 for non-existent column."""
        count = column_relation_repository.delete_relations_by_catalog_column(
            db, "nonexistent"
        )
        assert count == 0


class TestSelectRelationsByMetadataColumns:
    """Tests for select_relations_by_metadata_columns method."""

    def test_select_multiple(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
    ) -> None:
        """Should return relations for multiple metadata columns."""
        target_columns = ["dct:title", "dct:description"]
        result = column_relation_repository.select_relations_by_metadata_columns(
            db, target_columns
        )
        expected_count = sum(
            1 for r in sample_column_relations if r.metadata_column in target_columns
        )
        assert len(result) == expected_count

    def test_select_empty_list(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
    ) -> None:
        """Should return empty list for empty input."""
        result = column_relation_repository.select_relations_by_metadata_columns(
            db, []
        )
        assert result == []
