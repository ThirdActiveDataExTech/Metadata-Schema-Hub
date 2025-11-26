from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from app.config import settings
from app.log import Log
from app.version import VERSION

# Generic type variable for type-safe responses
T = TypeVar("T")


class APIResponseModel(BaseModel, Generic[T]):
    """기본 API 응답 포맷 by AIP Restful API 디자인 가이드

    AI플랫폼팀 API 정식 포맷으로 그대로 사용 권장

    Generic type parameter를 사용하여 type-safe한 response를 제공합니다.

    Examples:
        APIResponseModel[List[MetadataEntryResponse]]  # 목록 응답
        APIResponseModel[MetadataEntryResponse]  # 단일 객체 응답
        APIResponseModel[Dict[str, Any]]  # 동적 구조 응답
    """

    code: int = Field(default=int(f"{settings.SERVICE_CODE}200"))  # 6자리 숫자 권장
    message: str = Field(default=f"API Response Success ({VERSION})" if Log.is_debug_enable() else "API Response Success")
    result: Optional[T] = Field(default=None)  # Type-safe API response result
    description: str = Field(default="응답과 관련된 자세한 설명 작성")

    def to_dict(self):
        return {"code": self.code, "message": self.message, "result": self.result, "description": self.description}
