"""CatalogMerge exceptions."""

from typing import Any

from starlette import status

from app.config import settings
from app.exceptions.base import ApplicationError


class MergeError(ApplicationError):
    """Merge base exception."""

    def __init__(self, message: str = "MergeError", result: Any = None):
        """Initialize MergeError."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_500_INTERNAL_SERVER_ERROR}")
        self.message = message
        self.result = result


class MergeNotFoundError(MergeError):
    """Merge not found."""

    def __init__(self, merge_id: int, result: Any = None):
        """Initialize MergeNotFoundError."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_404_NOT_FOUND}")
        self.message = f"CatalogMerge not found: {merge_id}"
        self.result = result


class MergeNotPendingError(MergeError):
    """Merge is not in PENDING status."""

    def __init__(self, merge_id: int, current_decision: str, result: Any = None):
        """Initialize MergeNotPendingError."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.message = f"CatalogMerge {merge_id} is not PENDING: {current_decision}"
        self.result = result


class MergeNotApprovedError(MergeError):
    """Merge is not in APPROVED status (required for publish)."""

    def __init__(self, merge_id: int, current_decision: str, result: Any = None):
        """Initialize MergeNotApprovedError."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.message = f"CatalogMerge {merge_id} is not APPROVED: {current_decision}"
        self.result = result
