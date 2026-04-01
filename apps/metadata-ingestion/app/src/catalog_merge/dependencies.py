"""Dependency injection for CatalogMerge."""

from typing import Annotated

from fastapi import Depends

from app.src.catalog_entry.dependencies import get_catalog_entry_service
from app.src.catalog_entry.service import CatalogEntryService
from app.src.catalog_merge.repository import CatalogMergeRepository
from app.src.catalog_merge.service import CatalogMergeService
from app.src.events import EventBus
from app.src.events.dependencies import get_event_bus


def get_catalog_merge_repository() -> CatalogMergeRepository:
    """CatalogMergeRepository dependency."""
    return CatalogMergeRepository()


def get_catalog_merge_service(
    repository: Annotated[CatalogMergeRepository, Depends(get_catalog_merge_repository)],
    catalog_entry_service: Annotated[CatalogEntryService, Depends(get_catalog_entry_service)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
) -> CatalogMergeService:
    """CatalogMergeService dependency."""
    return CatalogMergeService(
        repository=repository,
        catalog_entry_service=catalog_entry_service,
        event_bus=event_bus,
    )


CatalogMergeServiceDep = Annotated[CatalogMergeService, Depends(get_catalog_merge_service)]
