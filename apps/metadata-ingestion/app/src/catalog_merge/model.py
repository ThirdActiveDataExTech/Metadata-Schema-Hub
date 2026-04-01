"""CatalogMerge models for metadata-ingestion app."""

from active_metadata.models import CatalogMergeBase
from pydantic import BaseModel, Field


class CatalogMerge(CatalogMergeBase, table=True):  # type: ignore[call-arg]
    """CatalogMerge table model."""

    __tablename__ = "catalog_merge"  # type: ignore[assignment]


# --- Pydantic DTOs for merge_evidence (3-key 패턴) ---


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
