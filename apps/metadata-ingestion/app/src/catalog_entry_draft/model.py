"""CatalogEntryDraft models for metadata-ingestion app."""

from datetime import date
from typing import Any

from active_metadata.models import CatalogEntryDraftBase
from pydantic import BaseModel


class CatalogEntryDraft(CatalogEntryDraftBase, table=True):  # type: ignore[call-arg]
    """CatalogEntryDraft table model."""

    __tablename__ = "catalog_entry_draft"  # type: ignore[assignment]


class MappingCandidate(BaseModel):
    """Single mapping candidate with evidence."""

    metadata_column: str
    correlation: float
    value: Any


class MappingEvidence(BaseModel):
    """Mapping evidence for a catalog field."""

    selected: MappingCandidate
    alternatives: list[MappingCandidate] = []


class CatalogEntryDraftCreate(BaseModel):
    """DTO for creating draft."""

    snapshot_id: str
    mapping_version: str
    title: str | None = None
    description: str | None = None
    issued: date | None = None
    modified: date | None = None
    publisher: str | None = None
    keyword: list[str] | None = None
    theme: list[str] | None = None
    landing_page: str | None = None
    access_url: str | None = None
    mapping_evidence: dict[str, Any] = {}
