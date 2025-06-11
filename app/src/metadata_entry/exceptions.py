from starlette import status

from app.config import settings
from app.exceptions.base import ApplicationError


class MetadataEntryError(ApplicationError):
    """MetadataEntry 예외"""

    def __init__(self):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_500_INTERNAL_SERVER_ERROR}")
        self.message = "MetadataEntryError"


class MetadataEntryNotSupportedTypeError(ApplicationError):
    """MetadataEntry Transform Not Supported Type error."""

    def __init__(self, type: str):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.message = f"{type=} Not Supported."
