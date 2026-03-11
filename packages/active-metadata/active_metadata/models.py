"""Shared database model definitions for metadata management.

Provides base SQLModel classes for metadata, catalog entries, and column relations.
These models define the core schema shared across metadata-ingestion and catalog-service.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP
from sqlmodel import Column, Field, SQLModel

from active_metadata.types import EntityURI, SnapshotIdentifier

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
    identifier: str = Field(nullable=False, default_factory=lambda: str(uuid4()))
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
    """Workflow state machine for ingestion process monitoring.

    Tracks the state of metadata ingestion workflows (STORED → DRAFTED or FAILED).
    Used for:
    - Monitoring pending/failed workflows
    - Identifying runs that need retry or investigation
    - Linking snapshot to draft via run lifecycle

    Note: This is operational data, not lineage. For data provenance, see LineageEventBase.
    """

    run_id: UUID | None = Field(default=None, primary_key=True)
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

    START = "START"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"


class LineageEventBase(SQLModel):
    """Immutable data provenance events for lineage tracking.

    Records the flow of data through the system:
    file → metadata_snapshot → catalog_entry_draft → catalog_entry

    Used for:
    - Upstream/downstream lineage queries (where did this data come from?)
    - Audit trail (who processed what, when?)
    - Lineage visualization in UI

    Note: This is append-only audit data. For workflow state, see IngestionRunBase.
    URI refs are generated via EntityURI.
    """

    id: int | None = Field(default=None, primary_key=True)
    event_time: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False),
    )
    event_type: LineageEventType = Field(nullable=False, default=LineageEventType.COMPLETE)
    job_name: str = Field(max_length=50, nullable=False)

    # URI 배열 참조
    input_refs: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String), nullable=False))
    output_refs: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String), nullable=False))

    # 선택적 메타데이터
    error_message: str | None = None

    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now()),
    )

    def extract_context(self) -> dict[str, Any]:
        """Extract context from URI refs.

        Parses URIs to extract:
        - snapshotId from {schema}.metadata_snapshot/{id}
        - draftId from {schema}.catalog_entry_draft/{id}
        - catalogEntryId from {schema}.catalog_entry/{id}
        - filename from file://{filename}

        Returns:
            Dict with snapshotId, draftId, catalogEntryId, filename (all nullable)
        """
        snapshot_id: str | None = None
        draft_id: int | None = None
        catalog_entry_id: int | None = None
        filename: str | None = None

        all_refs = (self.input_refs or []) + (self.output_refs or [])

        for ref in all_refs:
            schema, table, entity_id = EntityURI.parse(ref)

            if table == "metadata_snapshot" and not snapshot_id:
                snapshot_id = entity_id
            elif table == "catalog_entry_draft" and draft_id is None:
                try:
                    draft_id = int(entity_id)
                except ValueError:
                    pass
            elif table == "catalog_entry" and catalog_entry_id is None:
                try:
                    catalog_entry_id = int(entity_id)
                except ValueError:
                    pass
            elif table == "file" and not filename:
                filename = entity_id

        return {
            "snapshotId": snapshot_id,
            "draftId": draft_id,
            "catalogEntryId": catalog_entry_id,
            "filename": filename,
        }

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to API response dictionary.

        Includes base fields with datetime serialization and extracted context.

        Returns:
            Dict ready for JSON serialization
        """
        context = self.extract_context()
        return {
            "id": self.id,
            "eventTime": self.event_time.isoformat() if self.event_time else None,
            "eventType": self.event_type,
            "jobName": self.job_name,
            "inputRefs": self.input_refs,
            "outputRefs": self.output_refs,
            "snapshotId": context["snapshotId"],
            "draftId": context["draftId"],
            "catalogEntryId": context["catalogEntryId"],
            "filename": context["filename"],
            "errorMessage": self.error_message,
        }

    def to_graph_node(self) -> dict[str, Any]:
        """Convert to graph node dictionary for lineage visualization.

        Returns:
            Dict with node properties for graph rendering
        """
        context = self.extract_context()
        return {
            "id": f"job-{self.id}",
            "type": "run",
            "job": self.job_name,
            "eventType": self.event_type,
            "eventTime": self.event_time.isoformat() if self.event_time else None,
            "draftId": context["draftId"],
            "catalogEntryId": context["catalogEntryId"],
            "filename": context["filename"],
        }
