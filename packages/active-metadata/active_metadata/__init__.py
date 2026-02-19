"""Active Metadata Management - Shared Package.

Provides shared database models and utilities for metadata management apps.
"""

__version__ = "0.1.0"

from active_metadata.models import CatalogEntryBase, ColumnRelationBase, MetadataBase
from active_metadata.utils import to_str_list

__all__ = [
    "MetadataBase",
    "CatalogEntryBase",
    "ColumnRelationBase",
    "to_str_list",
]
