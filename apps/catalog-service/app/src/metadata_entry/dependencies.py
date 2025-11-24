from typing import Annotated

from fastapi import Depends

from app.src.metadata_entry.repository import MetadataEntryRepository
from app.src.metadata_entry.service import MetadataEntryService


def get_metadata_entry_repository() -> MetadataEntryRepository:
    """MetadataEntryRepository dependency injection."""
    return MetadataEntryRepository()


def get_metadata_entry_service(
    repository: Annotated[MetadataEntryRepository, Depends(get_metadata_entry_repository)],
) -> MetadataEntryService:
    """MetadataEntryService dependency injection."""
    return MetadataEntryService(repository)


MetadataEntryServiceDep = Annotated[MetadataEntryService, Depends(get_metadata_entry_service)]
