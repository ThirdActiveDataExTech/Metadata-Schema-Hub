"""Shared database model definitions for metadata management.

Provides base SQLModel classes for metadata, catalog entries, and column relations.
These models define the core schema shared across metadata-ingestion and catalog-service.
"""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import field_validator
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlmodel import Column, Field, SQLModel

__all__ = [
    "MetadataBase",
    "CatalogEntryBase",
    "ColumnRelationBase",
    "MetadataSnapshotBase",
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


class MetadataSnapshotBase(SQLModel):
    """Immutable metadata snapshot - base model."""

    snapshot_id: str = Field(primary_key=True)
    payload_sha256: str = Field(nullable=False, index=True)
    ingested_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    storage_key: str = Field(nullable=False)
    original_filename: str | None = None

    @field_validator("snapshot_id")
    @classmethod
    def validate_snapshot_id_format(cls, v: str) -> str:
        """Validate snapshot_id format: urn:{namespace}:metadata:{timestamp}-{hash[:12]}."""
        if not v.startswith("urn:"):
            raise ValueError("snapshot_id must start with 'urn:'")

        # Extract parts: urn:{namespace}:metadata:{timestamp}-{hash}
        try:
            parts = v.split(":", 3)
            if len(parts) != 4:
                raise ValueError("snapshot_id must have format 'urn:{namespace}:metadata:{timestamp}-{hash}'")

            namespace, resource_type, timestamp_hash = parts[1], parts[2], parts[3]

            # Validate namespace is alphanumeric with hyphens/underscores
            if not namespace or not all(c.isalnum() or c in "-_" for c in namespace):
                raise ValueError("Namespace must be alphanumeric (hyphens/underscores allowed)")

            # Validate resource type is "metadata"
            if resource_type != "metadata":
                raise ValueError("Resource type must be 'metadata'")

            timestamp_hash = parts[3]
            if "-" not in timestamp_hash:
                raise ValueError("snapshot_id must contain timestamp-hash format")

            timestamp_part, hash_part = timestamp_hash.split("-", 1)

            # Validate timestamp is numeric
            if not timestamp_part.isdigit():
                raise ValueError("Timestamp part must be numeric")

            # Validate hash is exactly 12 characters (hexadecimal)
            if len(hash_part) != 12:
                raise ValueError("Hash part must be exactly 12 characters")

            if not all(c in "0123456789abcdef" for c in hash_part.lower()):
                raise ValueError("Hash part must be hexadecimal")

        except (IndexError, AttributeError) as e:
            raise ValueError(f"Invalid snapshot_id format: {e}") from None

        return v

    @field_validator("payload_sha256")
    @classmethod
    def validate_payload_sha256_format(cls, v: str) -> str:
        """Validate payload_sha256 is valid SHA256 hash (64 hex characters)."""
        if len(v) != 64:
            raise ValueError("payload_sha256 must be exactly 64 characters (SHA256)")

        if not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("payload_sha256 must be hexadecimal")

        return v
