from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# ==================== Request Schemas ====================


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


class CatalogEntrySummaryResponse(BaseModel):
    """카탈로그 목록 응답 (간략 정보)"""

    id: int = Field(description="카탈로그 엔트리 ID", examples=[31])
    title: Optional[str] = Field(None, description="데이터셋 제목")
    issued: Optional[str] = Field(None, description="최초 발행일")
    modified: Optional[str] = Field(None, description="최종 수정일")
    identifier: str = Field(description="고유 식별자")
    publisher: Optional[str] = Field(None, description="발행처")
    keyword: Optional[List[str]] = Field(None, description="키워드 배열")
    landing_page: Optional[str] = Field(None, description="웹 페이지 URL")
    theme: Optional[List[str]] = Field(None, description="주제 분류")
    access_url: Optional[str] = Field(None, description="접근 URL")
    ingested_at: Optional[str] = Field(None, description="수집 시각")
    updated_at: Optional[str] = Field(None, description="갱신 시각")


class RawMetadataResponse(BaseModel):
    """원본 메타데이터 응답"""

    catalog_entry_id: int = Field(description="카탈로그 엔트리 ID")
    format: Literal["json", "xml"] = Field(description="메타데이터 형식")
    content: Any = Field(description="원본 메타데이터 내용")


class RdfResponse(BaseModel):
    """RDF 표현 응답 (JSON-LD)"""

    context: Dict[str, str] = Field(
        alias="@context",
        description="JSON-LD 컨텍스트",
        examples=[
            {
                "dcat": "http://www.w3.org/ns/dcat#",
                "dct": "http://purl.org/dc/terms/",
            }
        ],
    )
    graph: List[Dict[str, Any]] = Field(alias="@graph", description="RDF 그래프")
