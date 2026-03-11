"""FastAPI dependencies for lineage module."""

from typing import Annotated

from fastapi import Depends

from app.src.lineage.repository import LineageEventRepository
from app.src.lineage.service import LineageEventService
from app.src.lineage.writer import LineageWriter

__all__ = ["LineageEventServiceDep", "LineageWriterDep", "get_lineage_service"]


def get_lineage_writer() -> LineageWriter:
    """Get lineage writer instance (Separate TX pattern)."""
    return LineageWriter()


def get_lineage_repository() -> LineageEventRepository:
    """Get lineage event repository instance (for read operations)."""
    return LineageEventRepository()


def get_lineage_service(
    repository: Annotated[LineageEventRepository, Depends(get_lineage_repository)],
) -> LineageEventService:
    """Get lineage event service instance (read-only)."""
    return LineageEventService(repository=repository)


LineageWriterDep = Annotated[LineageWriter, Depends(get_lineage_writer)]
LineageEventServiceDep = Annotated[LineageEventService, Depends(get_lineage_service)]
