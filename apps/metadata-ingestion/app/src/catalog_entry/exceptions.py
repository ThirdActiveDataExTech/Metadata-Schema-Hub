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

    def __init__(self, message: str, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_404_NOT_FOUND}")
        self.result = result
        self.message = message

    @classmethod
    def by_id(cls, catalog_entry_id: int) -> "CatalogEntryNotFoundError":
        """Create exception for not found by ID."""
        return cls(f"CatalogEntry not found: id={catalog_entry_id}")

    @classmethod
    def by_identifier(cls, identifier: str) -> "CatalogEntryNotFoundError":
        """Create exception for not found by identifier."""
        return cls(f"CatalogEntry not found: identifier={identifier}")
