from typing import List

from sqlmodel import Session, select

from app.src.column_relation.model import ColumnRelation


class ColumnRelationRepository:
    """ColumnRelationRepository."""

    def select_relations_by_catalog_column(self, db: Session, catalog_column: str) -> List[ColumnRelation]:
        """Select relations by catalog column."""
        statement = (
            select(ColumnRelation)
            .where(ColumnRelation.catalog_column == catalog_column)
            .order_by(ColumnRelation.correlation.desc())  # pyright: ignore
        )
        results = db.exec(statement).all()
        return list(results)

    def select_relations_by_metadata_column(self, db: Session, metadata_column: str) -> List[ColumnRelation]:
        """Select relations by metadata column."""
        statement = (
            select(ColumnRelation)
            .where(ColumnRelation.metadata_column == metadata_column)
            .order_by(ColumnRelation.correlation.desc())  # pyright: ignore
        )
        results = db.exec(statement).all()
        return list(results)

    def select_relations_by_threshold(self, db: Session, min_correlation: float) -> List[ColumnRelation]:
        """Select relations above correlation threshold."""
        statement = (
            select(ColumnRelation)
            .where(ColumnRelation.correlation >= min_correlation)
            .order_by(ColumnRelation.correlation.desc())  # pyright: ignore
        )
        results = db.exec(statement).all()
        return list(results)

    def select_all_relations(self, db: Session) -> List[ColumnRelation]:
        """Select all column relations."""
        statement = select(ColumnRelation)
        results = db.exec(statement).all()
        return list(results)

    def select_relations_by_metadata_columns(self, db: Session, metadata_columns: List[str]) -> List[ColumnRelation]:
        """Select relations by metadata columns."""
        statement = (
            select(ColumnRelation)
            .where(ColumnRelation.metadata_column.in_(metadata_columns))  # pyright: ignore
            .order_by(
                ColumnRelation.catalog_column,
                ColumnRelation.correlation.desc(),  # pyright: ignore
            )
        )
        results = db.exec(statement).all()
        return list(results)
