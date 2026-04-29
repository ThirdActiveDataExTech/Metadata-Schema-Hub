"""CatalogMerge models for metadata-ingestion app."""

from active_metadata.agent_schemas import MergeCandidate, MergeDecided, MergeEvidence, MergeRecommendation
from active_metadata.models import CatalogMergeBase

# Re-export for backwards compatibility within the app
__all__ = [
    "CatalogMerge",
    "MergeCandidate",
    "MergeRecommendation",
    "MergeDecided",
    "MergeEvidence",
]


class CatalogMerge(CatalogMergeBase, table=True):  # type: ignore[call-arg]
    """CatalogMerge table model."""

    __tablename__ = "catalog_merge"  # type: ignore[assignment]
