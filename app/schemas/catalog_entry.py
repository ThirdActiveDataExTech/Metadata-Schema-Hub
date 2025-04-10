from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, ARRAY
from sqlmodel import SQLModel, Field, Column


class CatalogEntry(SQLModel, table=True):
    __tablename__: str = "catalog_entry"

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
    publisher: Optional[dict] = Field(
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
    raw_metadata: dict = Field(
        sa_column=Column(JSONB, nullable=False)
    )
    ingested_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(TIMESTAMP(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(TIMESTAMP(timezone=True), onupdate=datetime.now)
    )
