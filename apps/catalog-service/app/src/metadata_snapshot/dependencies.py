"""Dependency injection for MetadataSnapshot (read-only)."""

from typing import Annotated

from fastapi import Depends

from app.src.metadata_snapshot.filesystem_storage import FilesystemStorage
from app.src.metadata_snapshot.repository import MetadataSnapshotRepository
from app.src.metadata_snapshot.service import MetadataSnapshotService


def get_metadata_snapshot_repository() -> MetadataSnapshotRepository:
    """MetadataSnapshotRepository dependency."""
    return MetadataSnapshotRepository()


def get_filesystem_storage() -> FilesystemStorage:
    """FilesystemStorage dependency (read-only)."""
    return FilesystemStorage(base_path="./snapshots")


def get_metadata_snapshot_service(
    repository: Annotated[MetadataSnapshotRepository, Depends(get_metadata_snapshot_repository)],
    storage: Annotated[FilesystemStorage, Depends(get_filesystem_storage)],
) -> MetadataSnapshotService:
    """MetadataSnapshotService dependency."""
    return MetadataSnapshotService(repository=repository, storage=storage)


MetadataSnapshotServiceDep = Annotated[MetadataSnapshotService, Depends(get_metadata_snapshot_service)]
