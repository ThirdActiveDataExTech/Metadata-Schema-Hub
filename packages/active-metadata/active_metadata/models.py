"""Shared database model definitions for metadata management.

Provides base SQLModel classes for metadata, catalog entries, and column relations.
These models define the core schema shared across metadata-ingestion and catalog-service.
"""

import hashlib
import re
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any, ClassVar, Self

from pydantic import field_validator
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlmodel import Column, Field, SQLModel

__all__ = [
    "MetadataBase",
    "CatalogEntryBase",
    "ColumnRelationBase",
    "MetadataSnapshotBase",
    "IngestionRunState",
    "IngestionRunBase",
    "DraftStatus",
    "CatalogEntryDraftBase",
    "SnapshotIdentifier",
]


@dataclass
class SnapshotIdentifier:
    """Snapshot identifier components (generation result)."""

    snapshot_id: str
    timestamp: int
    payload_sha256: str

    def generate_storage_key(self, extension: str) -> str:
        """Generate storage_key path from identifier.

        Returns:
            "{YYYY}/{MM}/{DD}/{timestamp}-{hash[:12]}.{ext}"
        """
        dt = datetime.fromtimestamp(self.timestamp, tz=UTC)
        return f"{dt.year}/{dt.month:02d}/{dt.day:02d}/{self.timestamp}-{self.payload_sha256[:12]}.{extension}"

    @classmethod
    def generate(cls, payload: str | bytes, namespace: str = "wisenut") -> Self:
        """Generate snapshot identifier from payload.

        Args:
            payload: Content to generate identifier for
            namespace: URN namespace (default: "wisenut")

        Returns:
            SnapshotIdentifier with snapshot_id, timestamp, and payload_sha256
        """
        payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
        timestamp = int(time.time())
        payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
        snapshot_id = f"urn:{namespace}:metadata:{timestamp}-{payload_sha256[:12]}"

        return cls(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            payload_sha256=payload_sha256,
        )


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
    # Traceability field
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
        for field_name, value in self:
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
        for field_name, value in self:
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

    _SHA256_HEX_LENGTH: ClassVar[int] = 64
    _HEX_CHARS: ClassVar[frozenset[str]] = frozenset("0123456789abcdef")
    _SNAPSHOT_ID_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^urn:[a-zA-Z0-9_-]+:metadata:\d+-[0-9a-fA-F]{12}$"
    )

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

    @classmethod
    def _is_hex(cls, value: str, expected_length: int | None = None) -> bool:
        """Check if string is hexadecimal with optional length validation."""
        if expected_length is not None and len(value) != expected_length:
            return False
        return all(c in cls._HEX_CHARS for c in value.lower())

    @field_validator("snapshot_id")
    @classmethod
    def validate_snapshot_id_format(cls, v: str) -> str:
        """Validate snapshot_id format: urn:{namespace}:metadata:{timestamp}-{hash[:12]}."""
        if not cls._SNAPSHOT_ID_PATTERN.match(v):
            raise ValueError(
                "Invalid snapshot_id format. Expected: urn:{namespace}:metadata:{timestamp}-{hash12}"
            )
        return v

    @field_validator("payload_sha256")
    @classmethod
    def validate_payload_sha256_format(cls, v: str) -> str:
        """Validate payload_sha256 is valid SHA256 hash (64 hex characters)."""
        if not cls._is_hex(v, expected_length=cls._SHA256_HEX_LENGTH):
            raise ValueError(
                f"payload_sha256 must be exactly {cls._SHA256_HEX_LENGTH} hexadecimal characters"
            )
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
        for field_name, value in self:
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
        for field_name, value in self:
            if field_name in long_text_fields and value and len(value) > max_text_length:
                result[field_name] = value[:max_text_length] + "..."
            elif isinstance(value, (date, datetime)):
                result[field_name] = value.isoformat()
            else:
                result[field_name] = value
        return result
