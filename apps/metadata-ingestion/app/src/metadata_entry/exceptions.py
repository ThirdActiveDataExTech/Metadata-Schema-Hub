from typing import Any

from starlette import status

from app.config import settings
from app.exceptions.base import ApplicationError


class MetadataEntryError(ApplicationError):
    """MetadataEntry 예외"""

    def __init__(self, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_500_INTERNAL_SERVER_ERROR}")
        self.result = result
        self.message = "MetadataEntryError"


class MetadataEntryInvalidFormatError(ApplicationError):
    """MetadataEntry Invalid Format Error."""

    def __init__(self, format_type: str, message: str, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.result = result
        self.message = f"Invalid {format_type} format: {message}"


class MetadataEntryFileNotFoundError(ApplicationError):
    """MetadataEntry File Not Found error."""

    def __init__(self, message: str, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.result = result
        self.message = message


class MetadataEntryTooManyFileError(ApplicationError):
    """MetadataEntry File Too Many Found error."""

    def __init__(self, message: str, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.result = result
        self.message = message


class MetadataEntryNotSupportedTypeError(ApplicationError):
    """MetadataEntry Transform Not Supported Type error."""

    def __init__(self, type: str, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.result = result
        self.message = f"{type=} Not Supported."
