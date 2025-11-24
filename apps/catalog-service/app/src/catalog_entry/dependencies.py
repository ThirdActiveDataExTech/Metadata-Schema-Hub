from typing import Annotated

from fastapi import Depends

from app.src.catalog_entry.repository import CatalogEntryRepository
from app.src.catalog_entry.service import CatalogEntryService


def get_catalog_entry_repository() -> CatalogEntryRepository:
    """CatalogEntryRepository dependency injection."""
    return CatalogEntryRepository()


def get_catalog_entry_service(
    repository: Annotated[CatalogEntryRepository, Depends(get_catalog_entry_repository)],
) -> CatalogEntryService:
    """CatalogEntryService dependency injection."""
    return CatalogEntryService(repository)


CatalogEntryServiceDep = Annotated[CatalogEntryService, Depends(get_catalog_entry_service)]
