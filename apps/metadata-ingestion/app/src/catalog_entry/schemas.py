from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== Response Schemas ====================


class CatalogEntryResponse(BaseModel):
    """카탈로그 엔트리 상세 응답"""

    id: int = Field(description="카탈로그 엔트리 고유 ID", examples=[31])
    title: Optional[str] = Field(None, description="데이터셋 제목", examples=["교통 데이터"])
    description: Optional[str] = Field(None, description="데이터셋 설명", examples=["서울시 교통 데이터"])
    issued: Optional[date] = Field(None, description="최초 발행일", examples=["2024-01-01"])
    modified: Optional[date] = Field(None, description="최종 수정일", examples=["2024-12-01"])
    identifier: str = Field(description="DCAT 기준 고유 식별자", examples=["550e8400-e29b-41d4-a716-446655440000"])
    publisher: Optional[str] = Field(None, description="발행처", examples=["서울시"])
    keyword: Optional[List[str]] = Field(None, description="키워드 배열", examples=[["교통", "데이터"]])
    landing_page: Optional[str] = Field(None, description="웹 페이지 URL", examples=["https://example.com"])
    theme: Optional[List[str]] = Field(None, description="주제 분류", examples=[["TRAN", "ENVI"]])
    access_url: Optional[str] = Field(None, description="접근 URL", examples=["https://api.example.com/data"])
    raw_metadata: Dict[str, Any] = Field(description="원본 메타데이터 (JSONB)")
    ingested_at: Optional[datetime] = Field(None, description="데이터 수집 시각")
    updated_at: Optional[datetime] = Field(None, description="후처리/재매핑 갱신 시각")


class MetadataCreateSummary(BaseModel):
    """메타데이터 생성 요약 (bulk 수집 응답용)"""

    metadata_id: str = Field(description="메타데이터 UUID", examples=["18e6f7bc-5791-488a-bc7b-d78b18e51dcd"])
    total_entries: int = Field(description="생성된 엔트리 개수", examples=[15])
    ingested_at: datetime = Field(description="수집 시각")
