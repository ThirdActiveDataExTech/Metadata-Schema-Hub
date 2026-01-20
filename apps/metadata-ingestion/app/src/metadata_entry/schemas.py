from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.src.catalog_entry.schemas import CatalogEntryResponse, MetadataCreateSummary

# ==================== Request Schemas ====================


# ==================== Response Schemas ====================


class MappingCandidateResponse(BaseModel):
    """매핑 후보 응답"""

    catalog_column: str = Field(description="카탈로그 컬럼명", examples=["title"])
    correlation: float = Field(description="연관성 점수 (0.0~1.0)", examples=[0.95], ge=0.0, le=1.0)


class BulkIngestErrorResponse(BaseModel):
    """대량 수집 에러 응답"""

    filename: str = Field(description="에러 발생 파일명", examples=["metadata.json"])
    error: str = Field(description="에러 메시지", examples=["Unsupported file format"])


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


class IngestResponse(BaseModel):
    """메타데이터 수집 응답"""

    catalog_result: CatalogEntryResponse = Field(description="생성된 카탈로그 엔트리 (DCAT 표준 기반)")
    metadata_result: List[MetadataEntryResponse] = Field(description="생성된 메타데이터 엔트리 목록")


class IngestBulkResponse(BaseModel):
    """메타데이터 대량 수집 응답"""

    processed_count: int = Field(description="처리된 파일 개수", examples=[5])
    catalog_result: List[CatalogEntryResponse] = Field(description="생성된 카탈로그 엔트리 목록 (DCAT 표준 기반)")
    metadata_result: List[MetadataCreateSummary] = Field(description="생성된 메타데이터 생성 정보 목록")
    errors: List[BulkIngestErrorResponse] = Field(description="에러 목록")


class PreviewResponse(BaseModel):
    """메타데이터 미리보기 응답"""

    metadata: Dict[str, str] = Field(description="자동 매핑된 카탈로그 컬럼과 값")
    metadata_candidates: Dict[str, List[MappingCandidateResponse]] = Field(
        description="매핑 후보 목록 (메타데이터 스키마별 카탈로그 컬럼 후보 및 연관성 점수)"
    )
    untyped: Dict[str, str] = Field(description="매핑되지 않은 메타데이터 (스키마명 -> 값)")


class FilterKeyResponse(BaseModel):
    """필터 key 목록 응답"""

    filters: List[str] = Field(description="메타데이터 필터 key 목록", examples=[["publisher", "theme", "tags", "created_at"]])
