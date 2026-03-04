"""Ingestion run exceptions."""

from typing import Any

from starlette import status

from app.config import settings
from app.exceptions.base import ApplicationError


class IngestionRunError(ApplicationError):
    """Base exception for IngestionRun errors."""

    def __init__(self, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_500_INTERNAL_SERVER_ERROR}")
        self.result = result
        self.message = "IngestionRunError"


class IngestionRunNotFoundError(IngestionRunError):
    """IngestionRun not found."""

    def __init__(self, run_id: int, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_404_NOT_FOUND}")
        self.result = result
        self.message = f"IngestionRun not found: {run_id}"


class InvalidIngestionRunStateError(IngestionRunError):
    """IngestionRun is not in expected state."""

    def __init__(self, run_id: int, current_state: str, expected_state: str = "STORED", result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.result = result
        self.message = f"IngestionRun {run_id} is not in {expected_state} state: {current_state}"


class NoMetadataEntriesError(IngestionRunError):
    """No metadata entries found for snapshot."""

    def __init__(self, snapshot_id: str, result: Any = None):
        """Initialize Exceptions."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.result = result
        self.message = f"No metadata entries found for snapshot: {snapshot_id}"
