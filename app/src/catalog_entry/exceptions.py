from starlette import status

from app.config import settings
from app.exceptions.base import ApplicationError


class CatalogEntryError(ApplicationError):
    """Catalog Entry 예외"""

    def __init__(self):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_500_INTERNAL_SERVER_ERROR}")
        self.message = "CatalogEntryError"


class CatalogEntryServiceError(CatalogEntryError):
    """CatalogEntryService 예외"""
    def __init__(self, message: str):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.message = message


class CatalogEntryNotFoundError(CatalogEntryError):
    """Catalog Entry Not Found"""

    def __init__(self, catalog_entry_id: int):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_404_NOT_FOUND}")
        self.message = f"{catalog_entry_id=} CatalogEntry Not Found."
