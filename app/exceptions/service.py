"""서비스 자체 로직에 관한 커스텀 예외처리 작성"""

from starlette import status

from app.config import settings
from app.exceptions.base import ApplicationError


class TokenValidationError(ApplicationError):
    """유효하지 않은 토큰 설정"""

    def __init__(self, x_token):
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_401_UNAUTHORIZED}")
        self.message = "Invalid x-token header"
        self.result = {"current_x_token": x_token}


class CatalogEntryError(ApplicationError):
    """Catalog Entry 예외"""

    def __init__(self):
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_500_INTERNAL_SERVER_ERROR}")
        self.message = "CatalogEntryError"


class CatalogEntryNotFoundError(CatalogEntryError):
    """Catalog Entry Not Found"""

    def __init__(self, catalog_entry_id: int):
        self.code = int(f"{settings.SERVICE_CODE}{status.HTTP_404_NOT_FOUND}")
        self.message = f"{catalog_entry_id=} CatalogEntry Not Found."

