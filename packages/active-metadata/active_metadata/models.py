import uuid
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Column, Field, SQLModel

__all__ = ["MetadataBase", "CatalogEntryBase", "ColumnRelationBase"]


class MetadataBase(SQLModel):
    """Key-value metadata schema"""

    metadata_schema: str = Field(nullable=False)
    value: Optional[str] = None


class CatalogEntryBase(SQLModel):
    """DCAT-based catalog fields"""

    title: Optional[str] = None
    description: Optional[str] = None
    issued: Optional[date] = None
    modified: Optional[date] = None
    identifier: str = Field(nullable=False, default_factory=lambda: str(uuid.uuid4()))
    publisher: Optional[str] = None
    keyword: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    landing_page: Optional[str] = None
    theme: Optional[List[str]] = Field(default=None, sa_column=Column(ARRAY(String)))
    access_url: Optional[str] = None
    raw_metadata: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )


class ColumnRelationBase(SQLModel):
    """Column mapping with correlation weights"""

    catalog_column: str = Field(nullable=False)
    correlation: float = Field(nullable=False, ge=0.0, le=1.0)
    metadata_column: str = Field(nullable=False)
