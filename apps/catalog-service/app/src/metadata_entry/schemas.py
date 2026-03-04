from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MetadataEntryResponse(BaseModel):
    """메타데이터 엔트리 응답"""

    id: int = Field(description="엔트리 ID", examples=[1])
    metadata_id: str = Field(description="메타데이터 식별자 (URN)", examples=["urn:wisenut:metadata:1708675200-094fdfd8f7f8"])
    metadata_schema: str = Field(description="메타데이터 스키마명", examples=["dct:title"])
    value: Optional[str] = Field(None, description="메타데이터 값", examples=["교통 데이터"])
    ingested_at: datetime = Field(description="수집 시각")
