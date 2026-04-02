"""Dependency injection for workflow services."""

from typing import Annotated

from fastapi import Depends

from app.src.catalog_entry.dependencies import get_catalog_entry_service
from app.src.catalog_entry.service import CatalogEntryService
from app.src.catalog_entry_draft.dependencies import get_catalog_entry_draft_service
from app.src.catalog_entry_draft.service import CatalogEntryDraftService
from app.src.catalog_merge.dependencies import get_catalog_merge_service
from app.src.catalog_merge.service import CatalogMergeService
from app.src.column_relation.dependencies import get_column_relation_service
from app.src.column_relation.service import ColumnRelationService
from app.src.events import EventBus
from app.src.events.dependencies import get_event_bus
from app.src.ingestion_run.dependencies import get_ingestion_run_service
from app.src.ingestion_run.service import IngestionRunService
from app.src.metadata_entry.dependencies import get_metadata_entry_service
from app.src.metadata_entry.service import MetadataEntryService
from app.src.metadata_snapshot.dependencies import (
    get_filesystem_storage,
    get_metadata_snapshot_service,
)
from app.src.metadata_snapshot.filesystem_storage import FilesystemStorage
from app.src.metadata_snapshot.service import MetadataSnapshotService
from app.src.workflow.ingestion_workflow import IngestionWorkflowService
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


def get_ingestion_workflow_service(
    snapshot_service: Annotated[MetadataSnapshotService, Depends(get_metadata_snapshot_service)],
    metadata_entry_service: Annotated[MetadataEntryService, Depends(get_metadata_entry_service)],
    ingestion_run_service: Annotated[IngestionRunService, Depends(get_ingestion_run_service)],
    draft_service: Annotated[CatalogEntryDraftService, Depends(get_catalog_entry_draft_service)],
    column_relation_service: Annotated[ColumnRelationService, Depends(get_column_relation_service)],
    file_storage: Annotated[FilesystemStorage, Depends(get_filesystem_storage)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    catalog_merge_service: Annotated[CatalogMergeService, Depends(get_catalog_merge_service)],
    catalog_entry_service: Annotated[CatalogEntryService, Depends(get_catalog_entry_service)],
) -> IngestionWorkflowService:
    """IngestionWorkflowService dependency injection."""
    return IngestionWorkflowService(
        snapshot_service=snapshot_service,
        metadata_entry_service=metadata_entry_service,
        ingestion_run_service=ingestion_run_service,
        draft_service=draft_service,
        column_relation_service=column_relation_service,
        file_storage=file_storage,
        event_bus=event_bus,
        catalog_merge_service=catalog_merge_service,
        catalog_entry_service=catalog_entry_service,
    )


IngestionWorkflowServiceDep = Annotated[IngestionWorkflowService, Depends(get_ingestion_workflow_service)]
