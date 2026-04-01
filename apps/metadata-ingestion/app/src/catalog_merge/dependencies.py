"""Dependency injection for CatalogMerge."""

from typing import Annotated

from fastapi import Depends

from app.src.catalog_merge.repository import CatalogMergeRepository
from app.src.catalog_merge.service import CatalogMergeService


def get_catalog_merge_repository() -> CatalogMergeRepository:
    """CatalogMergeRepository dependency."""
    return CatalogMergeRepository()


def get_catalog_merge_service(
    repository: Annotated[CatalogMergeRepository, Depends(get_catalog_merge_repository)],
) -> CatalogMergeService:
    """CatalogMergeService dependency."""
    return CatalogMergeService(repository=repository)


CatalogMergeServiceDep = Annotated[CatalogMergeService, Depends(get_catalog_merge_service)]
