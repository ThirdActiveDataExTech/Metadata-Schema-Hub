"""Integration tests for ColumnRelationRepository."""

import pytest
from sqlmodel import Session

from app.src.column_relation.model import ColumnRelation
from app.src.column_relation.repository import ColumnRelationRepository
from tests.constants import CORRELATION_MEDIUM, CORRELATION_MIN, CORRELATION_MAX


class TestSelectRelationsByCatalogColumn:
    """Tests for select_relations_by_catalog_column method."""

    def test_select_by_catalog_column(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
    ) -> None:
        """Should return relations for given catalog column."""
        target_column = "title"
        result = column_relation_repository.select_relations_by_catalog_column(
            db, target_column
        )
        expected = [r for r in sample_column_relations if r.catalog_column == target_column]
        assert len(result) == len(expected)
        metadata_cols = {r.metadata_column for r in result}
        expected_cols = {r.metadata_column for r in expected}
        assert metadata_cols == expected_cols

    def test_select_ordered_by_correlation_desc(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
    ) -> None:
        """Should return relations ordered by correlation descending."""
        result = column_relation_repository.select_relations_by_catalog_column(
            db, "title"
        )

        correlations = [r.correlation for r in result]
        assert correlations == sorted(correlations, reverse=True)

    def test_select_nonexistent_column(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
    ) -> None:
        """Should return empty list for non-existent column."""
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
        """Should return relations for given metadata column."""
        relation = sample_column_relations[0]  # title -> dct:title
        result = column_relation_repository.select_relations_by_metadata_column(
            db, relation.metadata_column
        )

        assert len(result) == 1
        assert result[0].catalog_column == relation.catalog_column
        assert result[0].correlation == relation.correlation

    def test_select_nonexistent_metadata_column(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
    ) -> None:
        """Should return empty list for non-existent metadata column."""
        result = column_relation_repository.select_relations_by_metadata_column(
            db, "nonexistent"
        )
        assert result == []


class TestSelectRelationsByThreshold:
    """Tests for select_relations_by_threshold method."""

    @pytest.mark.parametrize(
        "threshold,expects_results",
        [
            pytest.param(CORRELATION_MEDIUM, True, id="medium_threshold"),
            pytest.param(CORRELATION_MIN, True, id="min_returns_all"),
            pytest.param(CORRELATION_MAX, False, id="max_returns_empty"),
        ],
    )
    def test_select_by_threshold(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
        threshold: float,
        expects_results: bool,
    ) -> None:
        """Should return relations based on correlation threshold."""
        result = column_relation_repository.select_relations_by_threshold(db, threshold)

        if threshold == CORRELATION_MAX:
            assert result == []
        elif threshold == CORRELATION_MIN:
            assert len(result) == len(sample_column_relations)
        else:
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

    def test_select_all_empty(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
    ) -> None:
        """Should return empty list when no relations."""
        result = column_relation_repository.select_all_relations(db)
        assert result == []


class TestSelectRelationsByMetadataColumns:
    """Tests for select_relations_by_metadata_columns method."""

    def test_select_by_multiple_columns(
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
        metadata_cols = {r.metadata_column for r in result}
        expected_cols = {r.metadata_column for r in sample_column_relations if r.metadata_column in target_columns}
        assert metadata_cols == expected_cols

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

    def test_select_partial_match(
        self,
        db: Session,
        column_relation_repository: ColumnRelationRepository,
        sample_column_relations: list[ColumnRelation],
    ) -> None:
        """Should return only existing relations."""
        result = column_relation_repository.select_relations_by_metadata_columns(
            db, ["dct:title", "nonexistent"]
        )

        assert len(result) == 1
        assert result[0].metadata_column == "dct:title"
