"""CatalogEntryDraft 예외 정의."""

from typing import Any

from starlette import status

from app.config import settings
from app.exceptions.base import ApplicationError


class DraftError(ApplicationError):
    """Draft 기본 예외."""

    def __init__(self, message: str = "DraftError", result: Any = None):
        """Initialize DraftError."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_500_INTERNAL_SERVER_ERROR}")
        self.message = message
        self.result = result


class DraftNotFoundError(DraftError):
    """Draft Not Found 예외."""

    def __init__(self, draft_id: int, result: Any = None):
        """Initialize DraftNotFoundError."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_404_NOT_FOUND}")
        self.message = f"Draft not found: {draft_id}"
        self.result = result


class DraftNotPendingError(DraftError):
    """Draft가 PENDING 상태가 아닐 때 예외."""

    def __init__(self, draft_id: int, current_status: str, result: Any = None):
        """Initialize DraftNotPendingError."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.message = f"Draft {draft_id} is not in PENDING status: {current_status}"
        self.result = result


class DraftFieldNotEditableError(DraftError):
    """편집 불가능한 필드 수정 시도 예외."""

    def __init__(self, field_name: str, result: Any = None):
        """Initialize DraftFieldNotEditableError."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.message = f"Field not editable: {field_name}"
        self.result = result


class DraftMetadataSchemaNotFoundError(DraftError):
    """Metadata schema가 존재하지 않을 때 예외."""

    def __init__(self, metadata_schema: str, result: Any = None):
        """Initialize DraftMetadataSchemaNotFoundError."""
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_400_BAD_REQUEST}")
        self.message = f"Metadata schema not found: {metadata_schema}"
        self.result = result
