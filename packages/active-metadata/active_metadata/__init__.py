"""Active Metadata Management - Shared Package.

Provides shared database models and utilities for metadata management apps.
"""

__version__ = "0.1.0"

from active_metadata.models import (
    CatalogEntryBase,
    CatalogEntryDraftBase,
    ColumnRelationBase,
    DraftStatus,
    MetadataBase,
    MetadataSnapshotBase,
)
from active_metadata.parsing import convert_field_types, detect_extension, parse_date, to_str_list
from active_metadata.types import SnapshotIdentifier

__all__ = [
    "MetadataBase",
    "CatalogEntryBase",
    "CatalogEntryDraftBase",
    "ColumnRelationBase",
    "MetadataSnapshotBase",
    "SnapshotIdentifier",
    "DraftStatus",
    "detect_extension",
    "parse_date",
    "to_str_list",
    "convert_field_types",
]
