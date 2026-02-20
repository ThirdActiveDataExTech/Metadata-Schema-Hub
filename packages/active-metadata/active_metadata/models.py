"""Shared database model definitions for metadata management.

Provides base SQLModel classes for metadata, catalog entries, and column relations.
These models define the core schema shared across metadata-ingestion and catalog-service.
"""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlmodel import Column, Field, SQLModel

__all__ = [
    "MetadataBase",
    "CatalogEntryBase",
    "ColumnRelationBase",
]


class MetadataBase(SQLModel):
    """Key-value metadata schema - base for MetadataEntry table."""

    id: int | None = Field(default=None, primary_key=True)
    metadata_schema: str = Field(nullable=False)
    value: str | None = None
    metadata_id: str = Field(nullable=False)
    ingested_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )


class CatalogEntryBase(SQLModel):
    """DCAT-based catalog fields - base for CatalogEntry table."""

    id: int | None = Field(default=None, primary_key=True)
    ingested_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )
    title: str | None = None
    description: str | None = None
    issued: date | None = None
    modified: date | None = None
    identifier: str = Field(nullable=False, default_factory=lambda: str(uuid.uuid4()))
    publisher: str | None = None
    keyword: list[str] | None = Field(default=None, sa_column=Column(ARRAY(String)))
    landing_page: str | None = None
    theme: list[str] | None = Field(default=None, sa_column=Column(ARRAY(String)))
    access_url: str | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))

    @classmethod
    def get_list_fields(cls) -> list[str]:
        """Return field names that are list[str] type.

        Returns:
            List of field names with list[str] type

        Note:
            Must be manually updated when schema changes
        """
        return ["keyword", "theme"]


class ColumnRelationBase(SQLModel):
    """Column mapping with correlation weights - base for ColumnRelation table."""

    id: int | None = Field(default=None, primary_key=True)
    catalog_column: str = Field(nullable=False)
    correlation: float = Field(nullable=False, ge=0.0, le=1.0)
    metadata_column: str = Field(nullable=False)
