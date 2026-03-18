"""CatalogEntryDraft models for metadata-ingestion app."""

from datetime import date
from typing import Any

from active_metadata.models import CatalogEntryDraftBase
from pydantic import BaseModel, Field


class CatalogEntryDraft(CatalogEntryDraftBase, table=True):  # type: ignore[call-arg]
    """CatalogEntryDraft table model."""

    __tablename__ = "catalog_entry_draft"  # type: ignore[assignment]


class MappingCandidate(BaseModel):
    """Single mapping candidate with evidence."""

    metadata_column: str = Field(..., min_length=1)
    correlation: float = Field(..., ge=0.0, le=1.0)
    value: Any


class DecidedMapping(BaseModel):
    """Final decided mapping for a catalog field.

    Attributes:
        metadata_column: Selected metadata schema key
        correlation: Correlation score (None if out of candidates)
        value: The actual value from metadata_entry
        out_of_candidates: True if selected from outside the candidates list
    """

    metadata_column: str = Field(..., min_length=1)
    correlation: float | None = None
    value: Any
    out_of_candidates: bool = False


class MappingEvidence(BaseModel):
    """Mapping evidence for a catalog field (3-key structure).

    Attributes:
        candidates: Top-k candidates from column_relation (immutable)
        recommended: Algorithm's top-1 recommendation (immutable, None if no candidates)
        decided: Final decided value (editable by user)
    """

    candidates: list[MappingCandidate]
    recommended: MappingCandidate | None = None
    decided: DecidedMapping


class DraftFieldUpdate(BaseModel):
    """Request to update a single draft field by selecting metadata_entry."""

    catalog_field: str = Field(..., min_length=1)
    metadata_schema: str = Field(..., min_length=1)


class DraftFieldsUpdateRequest(BaseModel):
    """Request to update multiple draft fields."""

    updates: list[DraftFieldUpdate]


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
