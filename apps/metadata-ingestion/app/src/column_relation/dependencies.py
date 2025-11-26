from typing import Annotated

from fastapi import Depends

from app.src.column_relation.repository import ColumnRelationRepository
from app.src.column_relation.service import ColumnRelationService


def get_column_relation_repository() -> ColumnRelationRepository:
    """ColumnRelationRepository dependency injection."""
    return ColumnRelationRepository()


def get_column_relation_service(
    repository: Annotated[ColumnRelationRepository, Depends(get_column_relation_repository)],
) -> ColumnRelationService:
    """ColumnRelationService dependency injection."""
    return ColumnRelationService(repository)


ColumnRelationServiceDep = Annotated[ColumnRelationService, Depends(get_column_relation_service)]
