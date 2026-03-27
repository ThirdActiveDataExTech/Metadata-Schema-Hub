"""Active Metadata Management - Shared Package.

Provides shared database models and utilities for metadata management apps.
"""

__version__ = "0.1.0"

from active_metadata.models import (
    CatalogContentFields,
    CatalogEntryBase,
    CatalogEntryDraftBase,
    ColumnRelationBase,
    DraftStatus,
    LineageEventBase,
    LineageEventType,
    MetadataBase,
    MetadataSnapshotBase,
)
from active_metadata.parsing import convert_field_types, detect_extension, parse_date, to_atomic_list, to_str_list
from active_metadata.types import EntityURI, SnapshotIdentifier

__all__ = [
    "MetadataBase",
    "CatalogContentFields",
    "CatalogEntryBase",
    "CatalogEntryDraftBase",
    "ColumnRelationBase",
    "MetadataSnapshotBase",
    "SnapshotIdentifier",
    "DraftStatus",
    "LineageEventBase",
    "LineageEventType",
    "EntityURI",
    "detect_extension",
    "parse_date",
    "to_str_list",
    "to_atomic_list",
    "convert_field_types",
]
