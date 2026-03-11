"""FastAPI dependencies for lineage module (catalog-service)."""

from typing import Annotated

from fastapi import Depends

from app.src.lineage.repository import LineageEventRepository
from app.src.lineage.service import LineageEventService

__all__ = ["LineageEventServiceDep", "get_lineage_service"]


def get_lineage_repository() -> LineageEventRepository:
    """Get lineage event repository instance."""
    return LineageEventRepository()


def get_lineage_service(
    repository: Annotated[LineageEventRepository, Depends(get_lineage_repository)],
) -> LineageEventService:
    """Get lineage event service instance."""
    return LineageEventService(repository)


LineageEventServiceDep = Annotated[LineageEventService, Depends(get_lineage_service)]
