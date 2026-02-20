import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import TIMESTAMP, func
from sqlmodel import SQLModel, Field, Column

from active_metadata.models import MetadataBase


class MetadataEntry(MetadataBase, table=True):  # type: ignore
    """실제 DB 테이블 모델."""

    __tablename__ = "metadata_entry"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    metadata_id: str = Field(nullable=False)
    ingested_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    metadata_schema: str = Field(default=dict, nullable=False)


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
