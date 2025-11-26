from typing import List

from pydantic import BaseModel, Field

# ==================== Request Schemas ====================


class ColumnRelationCreateParams(BaseModel):
    """컬럼 관계 생성 파라미터"""

    catalog_column: str = Field(
        description="카탈로그 테이블의 컬럼명",
        examples=["title", "description", "publisher"],
    )
    metadata_column: str = Field(
        description="메타데이터 테이블의 스키마명",
        examples=["dct:title", "schema:name", "dcat:keyword"],
    )
    correlation: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="컬럼 간 연관성 점수 (0.0-1.0)",
        examples=[0.95, 1.0, 0.85],
    )


# ==================== Response Schemas ====================


class ColumnRelationResponse(BaseModel):
    """컬럼 관계 응답"""

    id: int = Field(description="관계 ID", examples=[1])
    catalog_column: str = Field(description="카탈로그 컬럼명", examples=["title"])
    metadata_column: str = Field(description="메타데이터 스키마명", examples=["dct:title"])
    correlation: float = Field(description="연관성 점수", examples=[0.95])


class ColumnRelationListResponse(BaseModel):
    """컬럼 관계 목록 응답"""

    relations: List[ColumnRelationResponse] = Field(description="관계 목록")
    total: int = Field(description="전체 개수", examples=[5])
