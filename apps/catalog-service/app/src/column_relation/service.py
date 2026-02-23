from sqlmodel import Session

from app.src.column_relation.model import ColumnRelation
from app.src.column_relation.repository import ColumnRelationRepository


class ColumnRelationService:
    """ColumnRelationService."""

    def __init__(self, repository: ColumnRelationRepository):
        """Initialize Service."""
        self.repository = repository

    def get_relations_by_catalog_column(self, db: Session, catalog_column: str) -> list[ColumnRelation]:
        """Get relations by catalog column."""
        return self.repository.select_relations_by_catalog_column(db, catalog_column)

    def get_relations_by_metadata_column(self, db: Session, metadata_column: str) -> list[ColumnRelation]:
        """Get relations by metadata column."""
        return self.repository.select_relations_by_metadata_column(db, metadata_column)

    def get_relations_by_metadata_columns(self, db: Session, metadata_columns: list[str]) -> list[ColumnRelation]:
        """Get relations by metadata columns."""
        return self.repository.select_relations_by_metadata_columns(db, metadata_columns)

    def get_all_relations(self, db: Session) -> list[ColumnRelation]:
        """Get all column relations."""
        return self.repository.select_all_relations(db)
