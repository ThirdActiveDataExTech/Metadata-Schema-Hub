from typing import Any

from starlette import status

from app.config import settings
from app.exceptions.base import ApplicationError


class CatalogEntryError(ApplicationError):
    """Catalog Entry 예외"""

    def __init__(self, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_500_INTERNAL_SERVER_ERROR}")
        self.result = result
        self.message = "CatalogEntryError"


class CatalogEntryServiceError(CatalogEntryError):
    """CatalogEntryService 예외"""
    def __init__(self, message: str, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.result = result
        self.message = message


class CatalogEntryNotFoundError(CatalogEntryError):
    """Catalog Entry Not Found"""

    def __init__(self, catalog_entry_id: int, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_404_NOT_FOUND}")
        self.result = result
        self.message = f"{catalog_entry_id=} CatalogEntry Not Found."
