"""Dependency injection for CatalogEntryDraft."""

from typing import Annotated

from fastapi import Depends

from app.src.catalog_entry.dependencies import get_catalog_entry_service
from app.src.catalog_entry.service import CatalogEntryService
from app.src.catalog_entry_draft.repository import CatalogEntryDraftRepository
from app.src.catalog_entry_draft.service import CatalogEntryDraftService


def get_catalog_entry_draft_repository() -> CatalogEntryDraftRepository:
    """CatalogEntryDraftRepository dependency."""
    return CatalogEntryDraftRepository()


def get_catalog_entry_draft_service(
    repository: Annotated[CatalogEntryDraftRepository, Depends(get_catalog_entry_draft_repository)],
    catalog_entry_service: Annotated[CatalogEntryService, Depends(get_catalog_entry_service)],
) -> CatalogEntryDraftService:
    """CatalogEntryDraftService dependency (with CatalogEntryService for publish)."""
    return CatalogEntryDraftService(
        repository=repository,
        catalog_entry_service=catalog_entry_service,
    )


CatalogEntryDraftServiceDep = Annotated[
    CatalogEntryDraftService, Depends(get_catalog_entry_draft_service)
]
