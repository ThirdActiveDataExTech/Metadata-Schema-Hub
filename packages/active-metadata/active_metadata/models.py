"""Shared database model definitions for metadata management.

Provides base SQLModel classes for metadata, catalog entries, and column relations.
These models define the core schema shared across metadata-ingestion and catalog-service.
"""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import Any, ClassVar

from pydantic import field_validator
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlmodel import Column, Field, SQLModel

from active_metadata.types import SnapshotIdentifier

__all__ = [
    "MetadataBase",
    "CatalogEntryBase",
    "ColumnRelationBase",
    "MetadataSnapshotBase",
    "IngestionRunState",
    "IngestionRunBase",
    "DraftStatus",
    "CatalogEntryDraftBase",
    "LineageEventType",
    "LineageEventBase",
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
    # Traceability field - links to original metadata in FilesystemStorage
    latest_snapshot_id: str | None = None

    @classmethod
    def get_list_fields(cls) -> list[str]:
        """Return field names that are list[str] type."""
        return ["keyword", "theme"]

    @classmethod
    def get_date_fields(cls) -> list[str]:
        """Return field names that are date type."""
        return ["issued", "modified"]

    @classmethod
    def get_long_text_fields(cls) -> list[str]:
        """Return field names that should be truncated in summary views."""
        return ["description"]

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to API response dictionary with automatic date/datetime serialization."""
        result = {}
        # Use model_dump() for SQLModel compatibility (works for both table=True and regular models)
        data = self.model_dump() if hasattr(self, "model_dump") else dict(self)
        for field_name, value in data.items():
            if isinstance(value, (date, datetime)):
                result[field_name] = value.isoformat()
            else:
                result[field_name] = value
        return result

    def to_summary_dict(self, max_text_length: int = 100) -> dict[str, Any]:
        """Convert to summary dictionary with truncated long text fields.

        Args:
            max_text_length: Maximum length for long text fields before truncation

        Returns:
            Dict with all fields, long text fields truncated if needed
        """
        long_text_fields = self.get_long_text_fields()
        result = {}
        # Use model_dump() for SQLModel compatibility
        data = self.model_dump() if hasattr(self, "model_dump") else dict(self)
        for field_name, value in data.items():
            if field_name in long_text_fields and value and len(value) > max_text_length:
                result[field_name] = value[:max_text_length] + "..."
            elif isinstance(value, (date, datetime)):
                result[field_name] = value.isoformat()
            else:
                result[field_name] = value
        return result

    def get_rdf_dict(self) -> dict[str, Any]:
        """Convert catalog_entry to DCAT-based JSON-LD format.

        Returns:
            JSON-LD dictionary with @context and @graph containing Dataset and CatalogRecord.
        """
        # 1. Dataset (original data metadata)
        dataset: dict[str, Any] = {
            "@type": "dcat:Dataset",
            "@id": f"urn:dataset:{self.identifier}",
        }

        if self.title:
            dataset["dct:title"] = self.title
        if self.description:
            dataset["dct:description"] = self.description
        if self.identifier:
            dataset["dct:identifier"] = self.identifier
        if self.publisher:
            dataset["dct:publisher"] = {"@type": "foaf:Agent", "foaf:name": self.publisher}

        if self.issued:
            try:
                dataset["dct:issued"] = {"@type": "xsd:date", "@value": self.issued.isoformat()}
            except AttributeError:
                dataset["dct:issued"] = str(self.issued)

        if self.modified:
            try:
                dataset["dct:modified"] = {"@type": "xsd:date", "@value": self.modified.isoformat()}
            except AttributeError:
                dataset["dct:modified"] = str(self.modified)

        if self.keyword:
            dataset["dcat:keyword"] = self.keyword
        if self.theme:
            dataset["dcat:theme"] = self.theme
        if self.landing_page:
            dataset["dcat:landingPage"] = {"@type": "@id", "@id": self.landing_page}

        # Distribution (if access_url exists)
        if self.access_url:
            dataset["dcat:distribution"] = {
                "@type": "dcat:Distribution",
                "@id": f"urn:distribution:{self.identifier}",
                "dcat:accessURL": {"@type": "@id", "@id": self.access_url},
            }

        # 2. CatalogRecord (catalog system management info)
        catalog_record: dict[str, Any] = {
            "@type": "dcat:CatalogRecord",
            "@id": f"urn:catalog-record:{self.identifier}",
            "foaf:primaryTopic": {"@id": f"urn:dataset:{self.identifier}"},
        }

        if self.ingested_at:
            catalog_record["dct:issued"] = {"@type": "xsd:dateTime", "@value": self.ingested_at.isoformat()}
        if self.updated_at:
            catalog_record["dct:modified"] = {"@type": "xsd:dateTime", "@value": self.updated_at.isoformat()}

        # 3. Full structure (@graph pattern)
        return {
            "@context": {
                "dcat": "http://www.w3.org/ns/dcat#",
                "dct": "http://purl.org/dc/terms/",
                "foaf": "http://xmlns.com/foaf/0.1/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
            },
            "@graph": [dataset, catalog_record],
        }


class ColumnRelationBase(SQLModel):
    """Column mapping with correlation weights - base for ColumnRelation table."""

    id: int | None = Field(default=None, primary_key=True)
    catalog_column: str = Field(nullable=False)
    correlation: float = Field(nullable=False, ge=0.0, le=1.0)
    metadata_column: str = Field(nullable=False)


class MetadataSnapshotBase(SQLModel):
    """Immutable metadata snapshot - base model."""

    _HEX_CHARS: ClassVar[frozenset[str]] = frozenset("0123456789abcdef")

    snapshot_id: SnapshotIdentifier = Field(primary_key=True)
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

    @classmethod
    def _is_hex(cls, value: str, expected_length: int | None = None) -> bool:
        """Check if string is hexadecimal with optional length validation."""
        if expected_length is not None and len(value) != expected_length:
            return False
        return all(c in cls._HEX_CHARS for c in value.lower())

    @field_validator("payload_sha256")
    @classmethod
    def validate_payload_sha256_format(cls, v: str) -> str:
        """Validate payload_sha256 is valid SHA256 hash (64 hex characters)."""
        if not cls._is_hex(v, expected_length=SnapshotIdentifier.SHA256_HEX_LENGTH):
            raise ValueError(f"payload_sha256 must be exactly {SnapshotIdentifier.SHA256_HEX_LENGTH} hexadecimal characters")
        return v


class IngestionRunState(StrEnum):
    """Ingestion run workflow states."""

    STORED = "STORED"  # Store phase complete: payload stored
    DRAFTED = "DRAFTED"  # Draft phase complete: draft created
    FAILED = "FAILED"  # Processing failed


class DraftStatus(StrEnum):
    """Draft workflow states."""

    PENDING = "PENDING"  # Awaiting review
    PUBLISHED = "PUBLISHED"  # Published to catalog
    DISCARDED = "DISCARDED"  # Discarded by user


class IngestionRunBase(SQLModel):
    """Ingestion run job tracking - base model."""

    run_id: int | None = Field(default=None, primary_key=True)
    snapshot_id: str = Field(nullable=False, index=True)
    state: IngestionRunState = Field(default=IngestionRunState.STORED, nullable=False)
    mapping_version: str = Field(nullable=False)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )
    error: str | None = None
    draft_id: int | None = None


class CatalogEntryDraftBase(SQLModel):
    """Catalog entry draft with mapping evidence - base model."""

    id: int | None = Field(default=None, primary_key=True)
    snapshot_id: str = Field(nullable=False, index=True)
    mapping_version: str = Field(nullable=False, index=True)
    status: DraftStatus = Field(default=DraftStatus.PENDING, nullable=False)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )
    # Draft fields (mirrors catalog_entry)
    title: str | None = None
    description: str | None = None
    issued: date | None = None
    modified: date | None = None
    publisher: str | None = None
    keyword: list[str] | None = Field(default=None, sa_column=Column(ARRAY(String)))
    theme: list[str] | None = Field(default=None, sa_column=Column(ARRAY(String)))
    landing_page: str | None = None
    access_url: str | None = None
    # Mapping evidence (top-k candidates with scores)
    mapping_evidence: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))

    @classmethod
    def get_list_fields(cls) -> list[str]:
        """Return field names that are list[str] type."""
        return ["keyword", "theme"]

    @classmethod
    def get_date_fields(cls) -> list[str]:
        """Return field names that are date type."""
        return ["issued", "modified"]

    @classmethod
    def get_long_text_fields(cls) -> list[str]:
        """Return field names that should be truncated in summary views."""
        return ["description"]

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to API response dictionary with automatic date/datetime serialization."""
        result = {}
        # Use model_dump() for SQLModel compatibility (works for both table=True and regular models)
        data = self.model_dump() if hasattr(self, "model_dump") else dict(self)
        for field_name, value in data.items():
            if isinstance(value, (date, datetime)):
                result[field_name] = value.isoformat()
            else:
                result[field_name] = value
        return result

    def to_summary_dict(self, max_text_length: int = 100) -> dict[str, Any]:
        """Convert to summary dictionary with truncated long text fields.

        Args:
            max_text_length: Maximum length for long text fields before truncation

        Returns:
            Dict with all fields, long text fields truncated if needed
        """
        long_text_fields = self.get_long_text_fields()
        result = {}
        # Use model_dump() for SQLModel compatibility
        data = self.model_dump() if hasattr(self, "model_dump") else dict(self)
        for field_name, value in data.items():
            if field_name in long_text_fields and value and len(value) > max_text_length:
                result[field_name] = value[:max_text_length] + "..."
            elif isinstance(value, (date, datetime)):
                result[field_name] = value.isoformat()
            else:
                result[field_name] = value
        return result


class LineageEventType(StrEnum):
    """Lineage event types."""

    START = "START"  # OpenLineage Spec
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"  # OpenLineage Spec
    FAIL = "FAIL"  # OpenLineage Spec
    ABORT = "ABORT"  # OpenLineage Spec
    OTHER = "OTHER"


class LineageEventBase(SQLModel):
    """Lineage event base model - OpenLineage compatible.

    Stores lineage events for tracking metadata processing workflow.
    event_payload contains full OpenLineage RunEvent JSON.
    """

    id: int | None = Field(default=None, primary_key=True)
    event_time: datetime = Field(nullable=False)
    event_type: LineageEventType = Field(nullable=False)
    run_id: uuid.UUID = Field(nullable=False, index=True)
    job_namespace: str = Field(default="wisenut-amm", max_length=255)
    job_name: str = Field(max_length=255, nullable=False)
    event_payload: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    # Internal references for query optimization
    snapshot_id: str | None = None
    draft_id: int | None = None
    catalog_entry_id: int | None = None
    ingestion_run_id: int | None = None
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False),
    )
