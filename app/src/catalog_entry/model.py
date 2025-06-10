from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlmodel import Column, Field, SQLModel

KST = timezone(timedelta(hours=9))


class CatalogEntry(SQLModel, table=True):  # pyright: ignore
    """CatalogEntry 모델."""
    __tablename__: str = "catalog_entry"  # pyright: ignore

    id: Optional[int] = Field(
        default=None, primary_key=True
    )
    title: Optional[str] = None
    description: Optional[str] = None
    issued: Optional[date] = None
    modified: Optional[date] = None
    identifier: str = Field(
        nullable=False
    )
    publisher: Optional[str] = None
    keyword: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String))
    )
    landing_page: Optional[str] = None
    theme: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String))
    )
    access_url: Optional[str] = None
    raw_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False)
    )
    ingested_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )
    )


class CatalogEntrySummary(BaseModel):
    """카탈로그 목록 응답 DTO"""
    id: int
    title: Optional[str] = None
    issued: Optional[str] = None
    modified: Optional[str] = None
    identifier: str
    publisher: Optional[str] = None
    keyword: Optional[List[str]] = None
    landing_page: Optional[str] = None
    theme: Optional[List[str]] = None
    access_url: Optional[str] = None
    ingested_at: Optional[str] = None
    updated_at: Optional[str] = None


class CatalogEntryCreate(BaseModel):
    """카탈로그 생성 DTO"""
    identifier: str | None = None
    raw_metadata: Dict[str, Any]
    ingested_at: datetime = Field(default_factory=datetime.now)
