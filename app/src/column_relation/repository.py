from typing import List

from sqlalchemy import insert
from sqlmodel import select

from app.dependencies import SessionDep
from app.src.column_relation.model import ColumnRelation


class ColumnRelationRepository:
    """ColumnRelationRepository."""

    def save(self, db: SessionDep, column_relation: ColumnRelation) -> ColumnRelation:
        """Save column_relation."""
        db.add(column_relation)
        db.commit()
        db.refresh(column_relation)
        return column_relation

    def save_bulk(self, db: SessionDep, column_relations: List[ColumnRelation]) -> List[ColumnRelation]:
        """Save column_relations."""
        values = [
            {
                "catalog_column": relation.catalog_column,
                "correlation": relation.correlation,
                "metadata_column": relation.metadata_column
            }
            for relation in column_relations
        ]

        # 특정 컬럼만 returning
        stmt = insert(ColumnRelation).values(values).returning(  # pyright: ignore
            ColumnRelation.id,
            ColumnRelation.catalog_column,
            ColumnRelation.correlation,
            ColumnRelation.metadata_column
        )
        rows = db.exec(stmt).all()
        db.commit()

        # Row를 ColumnRelation으로 변환
        return [
            ColumnRelation(
                id=row.id,
                catalog_column=row.catalog_column,
                correlation=row.correlation,
                metadata_column=row.metadata_column
            )
            for row in rows
        ]

    def select_relations_by_catalog_column(self, db: SessionDep, catalog_column: str) -> List[ColumnRelation]:
        """Select relations by catalog column."""
        statement = (
            select(ColumnRelation)
            .where(ColumnRelation.catalog_column == catalog_column)
            .order_by(ColumnRelation.correlation.desc())  # pyright: ignore
        )
        results = db.exec(statement).all()
        return list(results)

    def select_relations_by_metadata_column(self, db: SessionDep, metadata_column: str) -> List[ColumnRelation]:
        """Select relations by metadata column."""
        statement = (
            select(ColumnRelation)
            .where(ColumnRelation.metadata_column == metadata_column)
            .order_by(ColumnRelation.correlation.desc())  # pyright: ignore
        )
        results = db.exec(statement).all()
        return list(results)

    def select_relations_by_threshold(self, db: SessionDep, min_correlation: float) -> List[ColumnRelation]:
        """Select relations above correlation threshold."""
        statement = (
            select(ColumnRelation)
            .where(ColumnRelation.correlation >= min_correlation)
            .order_by(ColumnRelation.correlation.desc())  # pyright: ignore
        )
        results = db.exec(statement).all()
        return list(results)

    def select_all_relations(self, db: SessionDep) -> List[ColumnRelation]:
        """Select all column relations."""
        statement = select(ColumnRelation)
        results = db.exec(statement).all()
        return list(results)

    def delete_relations_by_catalog_column(self, db: SessionDep, catalog_column: str) -> int:
        """Delete relations by catalog column. Returns deleted count."""
        statement = select(ColumnRelation).where(ColumnRelation.catalog_column == catalog_column)
        relations = db.exec(statement).all()
        count = len(relations)

        for relation in relations:
            db.delete(relation)
        db.commit()
        return count

    def select_relations_by_metadata_columns(self, db: SessionDep, metadata_columns: List[str]) -> List[ColumnRelation]:
        """Select relations by metadata columns."""
        statement = (
            select(ColumnRelation)
            .where(ColumnRelation.metadata_column.in_(metadata_columns))  # pyright: ignore
            .order_by(
                ColumnRelation.catalog_column,
                ColumnRelation.correlation.desc()  # pyright: ignore
            )
        )
        results = db.exec(statement).all()
        return list(results)
