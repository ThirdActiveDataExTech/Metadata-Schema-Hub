"""Dependency injection for IngestionRun."""

from typing import Annotated

from fastapi import Depends

from app.src.ingestion_run.repository import IngestionRunRepository
from app.src.ingestion_run.service import IngestionRunService


def get_ingestion_run_repository() -> IngestionRunRepository:
    """IngestionRunRepository dependency."""
    return IngestionRunRepository()


def get_ingestion_run_service(
    repository: Annotated[IngestionRunRepository, Depends(get_ingestion_run_repository)],
) -> IngestionRunService:
    """IngestionRunService dependency."""
    return IngestionRunService(repository=repository)


IngestionRunServiceDep = Annotated[IngestionRunService, Depends(get_ingestion_run_service)]
