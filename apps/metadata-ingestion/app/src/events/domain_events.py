"""Domain events for lineage tracking.

Business services publish these events. Handlers (e.g., LineageEventHandler)
subscribe and convert them to lineage events.

Benefits:
- Business logic doesn't know about lineage
- Easy to add audit/metrics handlers later
- Clean separation of concerns
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DomainEvent:
    """Base domain event."""

    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# Store Phase Events
# =============================================================================


@dataclass
class StorePhaseCompleted(DomainEvent):
    """Emitted when store phase completes successfully."""

    snapshot_id: str = ""
    metadata_count: int = 0
    original_filename: str | None = None


@dataclass
class StorePhaseFailed(DomainEvent):
    """Emitted when store phase fails."""

    error_message: str = ""
    original_filename: str | None = None


# =============================================================================
# Draft Phase Events
# =============================================================================


@dataclass
class DraftPhaseCompleted(DomainEvent):
    """Emitted when draft phase completes successfully."""

    snapshot_id: str = ""
    draft_id: int = 0


@dataclass
class DraftPhaseFailed(DomainEvent):
    """Emitted when draft phase fails."""

    snapshot_id: str = ""
    error_message: str = ""


# =============================================================================
# Merge Phase Events
# =============================================================================


@dataclass
class MergePhaseCompleted(DomainEvent):
    """Emitted when merge phase completes successfully."""

    snapshot_id: str = ""
    draft_id: int = 0
    merge_id: int = 0
    mapping_score: float = 0.0
    decided_by: str | None = None  # "system_auto" or None (manual pending)


@dataclass
class MergePhaseFailed(DomainEvent):
    """Emitted when merge phase fails."""

    snapshot_id: str = ""
    error_message: str = ""


# =============================================================================
# Publish Events
# =============================================================================


@dataclass
class PublishCompleted(DomainEvent):
    """Emitted when publish completes successfully."""

    draft_id: int = 0
    merge_id: int = 0
    catalog_entry_id: int = 0
    recommendation_followed: bool = True
    decided_by: str | None = None  # "system_auto" for auto-publish, user ID for manual


@dataclass
class DiscardCompleted(DomainEvent):
    """Emitted when discard completes successfully."""

    draft_id: int = 0
