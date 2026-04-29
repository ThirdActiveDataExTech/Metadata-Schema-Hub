"""Agent integration schemas — shared contract between ingestion service and external LangGraph agent.

These are pure Pydantic models (no SQLModel/DB dependencies).
Both the metadata-ingestion service and the external agent depend on this module.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# =============================================================================
# Mapping Evidence DTOs (moved from apps/metadata-ingestion)
# =============================================================================


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


# =============================================================================
# Merge Evidence DTOs (moved from apps/metadata-ingestion)
# =============================================================================


class MergeCandidate(BaseModel):
    """Single entity match candidate."""

    entry_id: int
    overlap_ids: list[str]
    updated_at: str | None = None  # ISO format


class MergeRecommendation(BaseModel):
    """Algorithm's recommended target."""

    entry_id: int
    reason: str = "most_recent"


class MergeDecided(BaseModel):
    """Final decided target."""

    entry_id: int
    decided_by: str  # "system_auto" or user ID


class MergeEvidence(BaseModel):
    """Merge evidence (3+1 key pattern: searched_external_ids + candidates/recommended/decided)."""

    searched_external_ids: list[str] = Field(default_factory=list)
    candidates: list[MergeCandidate] = Field(default_factory=list)
    recommended: MergeRecommendation | None = None
    decided: MergeDecided | None = None


# =============================================================================
# Agent API Contract — Draft Mapping
# =============================================================================


class AvailableMetadataItem(BaseModel):
    """Single metadata key-value available for agent selection."""

    metadata_schema: str  # e.g. "dc:title", "foaf:publisher"
    value: str | None


class DraftMappingRequest(BaseModel):
    """Request sent by ingestion service → agent for draft field re-mapping.

    The agent may select any metadata_schema from available_metadata,
    not limited to the candidates list in mapping_evidence.
    """

    draft_id: int
    snapshot_id: str
    mapping_evidence: dict[str, MappingEvidence]
    # key = catalog_field (e.g. "title", "description", "publisher")
    available_metadata: list[AvailableMetadataItem]
    # Full list of all metadata_schema/value pairs for this snapshot


class DraftMappingResponse(BaseModel):
    """Response from agent: decided field updates.

    Agent returns only fields it wants to change.
    Fields absent from updates retain their current decided value.

    Constraints (agent must enforce):
    - updates[*].metadata_schema must exist in DraftMappingRequest.available_metadata
    - updates[*].catalog_field must be a valid CatalogContentField
    """

    draft_id: int
    updates: list[DraftFieldUpdate]


# =============================================================================
# Agent API Contract — Merge Analysis
# =============================================================================


class MergeAnalysisRequest(BaseModel):
    """Request sent by ingestion service → agent for merge re-analysis."""

    merge_id: int
    draft_id: int
    mapping_score: float = Field(ge=0.0, le=1.0)
    merge_evidence: MergeEvidence
    draft_mapping_evidence: dict[str, MappingEvidence]
    # Included so the agent can read decided.value per field (title, description, etc.)
    # to understand dataset identity before deciding on a merge target


class MergeAnalysisResponse(BaseModel):
    """Response from agent: merge decision.

    Constraints (agent must enforce):
    - target_entry_id must be an entry_id from merge_evidence.candidates, or None
    - None target_entry_id with decision="approve" means create a new catalog entry
    """

    merge_id: int
    decision: Literal["approve", "reject", "defer"]
    target_entry_id: int | None = None
    decided_by: str = "langgraph_agent"
    reason: str
    # Human-readable explanation stored in response body for UI display and lineage audit
