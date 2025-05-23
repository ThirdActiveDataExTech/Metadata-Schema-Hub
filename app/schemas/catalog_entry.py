from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlmodel import Column, Field, SQLModel

KST = timezone(timedelta(hours=9))

class CatalogEntry(SQLModel, table=True):  # pyright: ignore
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
    publisher: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB)
    )
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
        sa_column=Column(JSONB, nullable=False)
    )
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(KST),
        sa_column=Column(TIMESTAMP(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(KST),
        sa_column=Column(TIMESTAMP(timezone=True), onupdate=lambda: datetime.now(KST))
    )
