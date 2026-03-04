"""Dependency injection for CatalogEntryDraft (read-only)."""

from typing import Annotated

from fastapi import Depends

from app.src.catalog_entry_draft.repository import CatalogEntryDraftRepository
from app.src.catalog_entry_draft.service import CatalogEntryDraftService


def get_catalog_entry_draft_repository() -> CatalogEntryDraftRepository:
    """CatalogEntryDraftRepository dependency."""
    return CatalogEntryDraftRepository()


def get_catalog_entry_draft_service(
    repository: Annotated[CatalogEntryDraftRepository, Depends(get_catalog_entry_draft_repository)],
) -> CatalogEntryDraftService:
    """CatalogEntryDraftService dependency."""
    return CatalogEntryDraftService(repository=repository)


CatalogEntryDraftServiceDep = Annotated[CatalogEntryDraftService, Depends(get_catalog_entry_draft_service)]
