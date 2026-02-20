import uuid
from datetime import datetime
from typing import List, Optional

from active_metadata.models import MetadataBase
from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class MetadataSchema(BaseModel):
    """파일 파싱 결과 - schema-value 쌍 (Converter 출력)"""

    metadata_schema: str
    value: str


class MetadataEntry(MetadataBase, table=True):  # type: ignore
    """실제 DB 테이블 모델."""

    __tablename__ = "metadata_entry"  # type: ignore


class MetadataCreate(SQLModel):
    """메타데이터 생성용 모델 - Converter 출력을 DB Entry로 변환."""

    metadata_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata_schemas: List[MetadataSchema]
    ingested_at: Optional[datetime] = None

    def get_metadata_entries(self) -> List[MetadataEntry]:
        """MetadataSchema 리스트를 MetadataEntry 리스트로 변환."""
        return [
            MetadataEntry(
                metadata_id=self.metadata_id,
                metadata_schema=schema.metadata_schema,
                value=schema.value,
            )
            for schema in self.metadata_schemas
        ]
