import uuid
from datetime import datetime
from typing import List, Optional

from active_metadata.models import MetadataBase
from sqlmodel import Field, SQLModel


class MetadataEntry(MetadataBase, table=True):  # type: ignore
    """실제 DB 테이블 모델."""

    __tablename__ = "metadata_entry"  # type: ignore


class MetadataCreate(SQLModel):
    """메타데이터 생성용 모델."""

    metadata_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata_bases: List[MetadataBase]
    ingested_at: Optional[datetime] = None

    def get_metadata_entries(self) -> List[MetadataEntry]:
        """MetadataBase 리스트를 MetadataEntry 리스트로 변환."""
        return [
            MetadataEntry(
                metadata_id=self.metadata_id,
                metadata_schema=item.metadata_schema,
                value=item.value,
            )
            for item in self.metadata_bases
        ]
