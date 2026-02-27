"""Dependency injection for MetadataSnapshot."""

from typing import Annotated

from fastapi import Depends

from app.config import settings
from app.src.metadata_snapshot.filesystem_storage import FilesystemStorage
from app.src.metadata_snapshot.repository import MetadataSnapshotRepository
from app.src.metadata_snapshot.service import MetadataSnapshotService


def get_metadata_snapshot_repository() -> MetadataSnapshotRepository:
    """MetadataSnapshotRepository dependency."""
    return MetadataSnapshotRepository()


def get_filesystem_storage() -> FilesystemStorage:
    """FilesystemStorage dependency."""
    return FilesystemStorage(base_path=settings.SNAPSHOT_STORAGE_PATH)


def get_metadata_snapshot_service(
    repository: Annotated[MetadataSnapshotRepository, Depends(get_metadata_snapshot_repository)],
) -> MetadataSnapshotService:
    """MetadataSnapshotService dependency."""
    return MetadataSnapshotService(repository=repository)


MetadataSnapshotServiceDep = Annotated[MetadataSnapshotService, Depends(get_metadata_snapshot_service)]
