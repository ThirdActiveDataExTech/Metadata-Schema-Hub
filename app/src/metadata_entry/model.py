from datetime import datetime
from typing import Optional

from sqlalchemy import TIMESTAMP, func
from sqlmodel import SQLModel, Field, Column


class MetadataBase(SQLModel):
    """공통 필드를 정의한 베이스 모델"""
    metadata_schema: str = Field(nullable=False)
    value: Optional[str] = None


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
        )
    )
    metadata_schema: str = Field(default=dict, nullable=False)
