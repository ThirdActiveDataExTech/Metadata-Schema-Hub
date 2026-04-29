"""Active Metadata Management - Shared Package.

Provides shared database models and utilities for metadata management apps.
"""

__version__ = "0.1.0"

from active_metadata.agent_schemas import (
    AvailableMetadataItem,
    DecidedMapping,
    DraftFieldUpdate,
    DraftMappingRequest,
    DraftMappingResponse,
    MappingCandidate,
    MappingEvidence,
    MergeAnalysisRequest,
    MergeAnalysisResponse,
    MergeCandidate,
    MergeDecided,
    MergeEvidence,
    MergeRecommendation,
)
from active_metadata.models import (
    CatalogContentFields,
    CatalogEntryBase,
    CatalogEntryDraftBase,
    CatalogMergeBase,
    ColumnRelationBase,
    DraftStatus,
    LineageEventBase,
    LineageEventType,
    MergeDecision,
    MetadataBase,
    MetadataSnapshotBase,
)
from active_metadata.parsing import convert_field_types, detect_extension, parse_date, to_atomic_list, to_str_list
from active_metadata.types import EntityURI, SnapshotIdentifier

__all__ = [
    # DB models
    "MetadataBase",
    "CatalogContentFields",
    "CatalogEntryBase",
    "CatalogEntryDraftBase",
    "CatalogMergeBase",
    "ColumnRelationBase",
    "MergeDecision",
    "MetadataSnapshotBase",
    "DraftStatus",
    "LineageEventBase",
    "LineageEventType",
    # Types
    "SnapshotIdentifier",
    "EntityURI",
    # Parsing utilities
    "detect_extension",
    "parse_date",
    "to_str_list",
    "to_atomic_list",
    "convert_field_types",
    # Agent schemas — mapping evidence DTOs
    "MappingCandidate",
    "DecidedMapping",
    "MappingEvidence",
    "DraftFieldUpdate",
    # Agent schemas — merge evidence DTOs
    "MergeCandidate",
    "MergeRecommendation",
    "MergeDecided",
    "MergeEvidence",
    # Agent schemas — API contract
    "AvailableMetadataItem",
    "DraftMappingRequest",
    "DraftMappingResponse",
    "MergeAnalysisRequest",
    "MergeAnalysisResponse",
]
