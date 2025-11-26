"""Workflow domain dependencies."""

from typing import Annotated

from fastapi import Depends

from app.src.catalog_entry.dependencies import get_catalog_entry_service
from app.src.catalog_entry.service import CatalogEntryService
from app.src.column_relation.dependencies import get_column_relation_service
from app.src.column_relation.service import ColumnRelationService
from app.src.metadata_entry.dependencies import get_metadata_entry_service
from app.src.metadata_entry.service import MetadataEntryService
from app.src.workflow.transform_service import CatalogEntryTransformService


def get_catalog_entry_transform_service(
    catalog_entry_service: Annotated[CatalogEntryService, Depends(get_catalog_entry_service)],
    column_relation_service: Annotated[ColumnRelationService, Depends(get_column_relation_service)],
    metadata_entry_service: Annotated[MetadataEntryService, Depends(get_metadata_entry_service)],
) -> CatalogEntryTransformService:
    """CatalogEntryTransformService dependency injection."""
    return CatalogEntryTransformService(
        catalog_entry_service=catalog_entry_service,
        column_relation_service=column_relation_service,
        metadata_entry_service=metadata_entry_service,
    )


CatalogEntryTransformServiceDep = Annotated[CatalogEntryTransformService, Depends(get_catalog_entry_transform_service)]
