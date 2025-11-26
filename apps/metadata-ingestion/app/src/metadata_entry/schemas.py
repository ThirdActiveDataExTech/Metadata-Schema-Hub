from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== Request Schemas ====================


# ==================== Response Schemas ====================


class MetadataEntryResponse(BaseModel):
    """메타데이터 엔트리 응답"""

    id: int = Field(description="엔트리 ID", examples=[1])
    metadata_id: str = Field(description="메타데이터 UUID", examples=["18e6f7bc-5791-488a-bc7b-d78b18e51dcd"])
    metadata_schema: str = Field(description="메타데이터 스키마명", examples=["dct:title"])
    value: Optional[str] = Field(None, description="메타데이터 값", examples=["교통 데이터"])
    ingested_at: datetime = Field(description="수집 시각")


class MetadataBaseResponse(BaseModel):
    """메타데이터 베이스 응답 (변환 결과)"""

    metadata_schema: str = Field(description="메타데이터 스키마명", examples=["dct:title"])
    value: Optional[str] = Field(None, description="메타데이터 값", examples=["교통 데이터"])


class ConvertResponse(BaseModel):
    """메타데이터 변환 응답"""

    metadata_bases: List[MetadataBaseResponse] = Field(description="변환된 메타데이터 목록")
    total: int = Field(description="전체 개수", examples=[10])


class IngestResponse(BaseModel):
    """메타데이터 수집 응답"""

    catalog_result: Any = Field(description="생성된 카탈로그 엔트리 (DCAT 표준 기반)")
    metadata_result: List[MetadataEntryResponse] = Field(description="생성된 메타데이터 엔트리 목록")


class IngestBulkResponse(BaseModel):
    """메타데이터 대량 수집 응답"""

    processed_count: int = Field(description="처리된 파일 개수", examples=[5])
    catalog_result: List[Any] = Field(description="생성된 카탈로그 엔트리 목록 (DCAT 표준 기반)")
    metadata_result: List[Any] = Field(description="생성된 메타데이터 생성 정보 목록")
    errors: List[Dict[str, Any]] = Field(description="에러 목록")


class PreviewResponse(BaseModel):
    """메타데이터 미리보기 응답"""

    metadata: Dict[str, str] = Field(description="자동 매핑된 카탈로그 컬럼과 값")
    metadata_candidates: Dict[str, List[Dict[str, Any]]] = Field(description="매핑 후보 목록 (연관성 점수 포함)")
    untyped: Dict[str, str] = Field(description="매핑되지 않은 메타데이터")
