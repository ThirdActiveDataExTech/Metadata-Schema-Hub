from typing import List, Tuple

from app.dependencies import SessionDep
from app.schemas.column_relation import ColumnRelation, ColumnRelationBase
from app.src.column_relation.repository import ColumnRelationRepository


class ColumnRelationService:
    """ColumnRelationService."""

    def __init__(self, repository: ColumnRelationRepository):
        """Initialize Service."""
        self.repository = repository

    def create_single_relation(
            self,
            db: SessionDep,
            relation: ColumnRelationBase
    ) -> ColumnRelation:
        """Create single column relation."""
        return self.repository.save(db, relation.to_table_model())

    def create_relations(
            self,
            db: SessionDep,
            relations: List[ColumnRelationBase]
    ) -> List[ColumnRelation]:
        """Create ColumnRelation from ML prediction results.

        Args:
            db: Database session
            relations: List of ColumnRelations (catalog_column, metadata_column, correlation)
        """
        return self.repository.save_bulk(db, [relation.to_table_model() for relation in relations])

    def get_relations_by_catalog_column(self, db: SessionDep, catalog_column: str) -> List[ColumnRelation]:
        """Get relations by catalog column."""
        return self.repository.select_relations_by_catalog_column(db, catalog_column)

    def get_relations_by_metadata_column(self, db: SessionDep, metadata_column: str) -> List[ColumnRelation]:
        """Get relations by metadata column."""
        return self.repository.select_relations_by_metadata_column(db, metadata_column)

    def get_all_relations(self, db: SessionDep) -> List[ColumnRelation]:
        """Get all column relations."""
        return self.repository.select_all_relations(db)

    def replace_catalog_relations(
            self,
            db: SessionDep,
            catalog_column: str,
            new_predictions: List[Tuple[str, float]]
    ) -> List[ColumnRelation]:
        """Replace all relations for a catalog column with new predictions.

        Args:
            db: Database session
            catalog_column: Target catalog column
            new_predictions: List of (metadata_column, correlation) tuples
        """
        # Delete existing relations
        self.repository.delete_relations_by_catalog_column(db, catalog_column)

        # Create new relations
        relations = [
            ColumnRelation(
                catalog_column=catalog_column,
                correlation=correlation,
                metadata_column=metadata_col
            )
            for metadata_col, correlation in new_predictions
        ]

        return self.repository.save_bulk(db, relations)
