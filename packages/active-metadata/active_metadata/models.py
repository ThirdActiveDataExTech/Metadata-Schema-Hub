"""Shared database model definitions for metadata management.

Provides base SQLModel classes for metadata, catalog entries, and column relations.
These models define the core schema shared across metadata-ingestion and catalog-service.
"""

import uuid
from datetime import date
from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Column, Field, SQLModel

__all__ = ["MetadataBase", "CatalogEntryBase", "ColumnRelationBase"]


class MetadataBase(SQLModel):
    """Key-value metadata schema."""

    metadata_schema: str = Field(nullable=False)
    value: str | None = None


class CatalogEntryBase(SQLModel):
    """DCAT-based catalog fields."""

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


class ColumnRelationBase(SQLModel):
    """Column mapping with correlation weights."""

    catalog_column: str = Field(nullable=False)
    correlation: float = Field(nullable=False, ge=0.0, le=1.0)
    metadata_column: str = Field(nullable=False)
