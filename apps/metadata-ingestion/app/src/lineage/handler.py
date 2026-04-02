"""Lineage event handler - converts domain events to lineage events.

This handler subscribes to domain events and emits lineage events.
Business services don't need to know about lineage - they just publish domain events.
"""

from __future__ import annotations

import logging

from active_metadata.models import LineageEventType
from active_metadata.types import EntityURI

from app.src.events.bus import EventBus
from app.src.events.domain_events import (
    DiscardCompleted,
    DraftPhaseCompleted,
    DraftPhaseFailed,
    MergePhaseCompleted,
    MergePhaseFailed,
    PublishCompleted,
    StorePhaseCompleted,
    StorePhaseFailed,
)
from app.src.lineage.model import LineageEvent
from app.src.lineage.writer import LineageWriter

logger = logging.getLogger(__name__)


class LineageEventHandler:
    """Converts domain events to lineage events and saves them.

    Subscribes to COMPLETE/FAIL domain events via EventBus.
    Uses LineageWriter for best-effort persistence (independent TX).
    Uses EntityURI classmethods for URI generation.

    Note: START events are not tracked - they provide no additional
    information for lineage graphs and create dead-end nodes.
    """

    def __init__(self, writer: LineageWriter) -> None:
        """Initialize with LineageWriter for persistence."""
        self.writer = writer

    # ========================================================================
    # Store Phase Handlers
    # ========================================================================

    def on_store_completed(self, event: StorePhaseCompleted) -> None:
        """Handle StorePhaseCompleted event."""
        lineage_event = LineageEvent(
            event_type=LineageEventType.COMPLETE,
            job_name="store-phase",
            input_refs=[EntityURI.file(event.original_filename or "unknown")],
            output_refs=[EntityURI.snapshot(event.snapshot_id)],
        )
        self.writer.save(lineage_event)

    def on_store_failed(self, event: StorePhaseFailed) -> None:
        """Handle StorePhaseFailed event."""
        lineage_event = LineageEvent(
            event_type=LineageEventType.FAIL,
            job_name="store-phase",
            input_refs=[EntityURI.file(event.original_filename or "unknown")],
            output_refs=[],
            error_message=event.error_message,
        )
        self.writer.save(lineage_event)

    # ========================================================================
    # Draft Phase Handlers
    # ========================================================================

    def on_draft_completed(self, event: DraftPhaseCompleted) -> None:
        """Handle DraftPhaseCompleted event."""
        lineage_event = LineageEvent(
            event_type=LineageEventType.COMPLETE,
            job_name="draft-phase",
            input_refs=[EntityURI.snapshot(event.snapshot_id)],
            output_refs=[EntityURI.draft(event.draft_id)],
        )
        self.writer.save(lineage_event)

    def on_draft_failed(self, event: DraftPhaseFailed) -> None:
        """Handle DraftPhaseFailed event."""
        lineage_event = LineageEvent(
            event_type=LineageEventType.FAIL,
            job_name="draft-phase",
            input_refs=[EntityURI.snapshot(event.snapshot_id)],
            output_refs=[],
            error_message=event.error_message,
        )
        self.writer.save(lineage_event)

    # ========================================================================
    # Merge Phase Handlers
    # ========================================================================

    def on_merge_completed(self, event: MergePhaseCompleted) -> None:
        """Handle MergePhaseCompleted event."""
        lineage_event = LineageEvent(
            event_type=LineageEventType.COMPLETE,
            job_name="merge-phase",
            input_refs=[EntityURI.draft(event.draft_id)],
            output_refs=[EntityURI.merge(event.merge_id)],
        )
        self.writer.save(lineage_event)

    def on_merge_failed(self, event: MergePhaseFailed) -> None:
        """Handle MergePhaseFailed event."""
        lineage_event = LineageEvent(
            event_type=LineageEventType.FAIL,
            job_name="merge-phase",
            input_refs=[EntityURI.snapshot(event.snapshot_id)],
            output_refs=[],
            error_message=event.error_message,
        )
        self.writer.save(lineage_event)

    # ========================================================================
    # Publish Handlers
    # ========================================================================

    def on_publish_completed(self, event: PublishCompleted) -> None:
        """Handle PublishCompleted event."""
        lineage_event = LineageEvent(
            event_type=LineageEventType.COMPLETE,
            job_name="publish",
            input_refs=[EntityURI.merge(event.merge_id)],
            output_refs=[EntityURI.catalog(event.catalog_entry_id)],
        )
        self.writer.save(lineage_event)

    def on_discard_completed(self, event: DiscardCompleted) -> None:
        """Handle DiscardCompleted event."""
        lineage_event = LineageEvent(
            event_type=LineageEventType.COMPLETE,
            job_name="discard",
            input_refs=[EntityURI.draft(event.draft_id)],
            output_refs=[],
        )
        self.writer.save(lineage_event)


def register_lineage_handlers(bus: EventBus, handler: LineageEventHandler) -> None:
    """Register lineage event handlers to the event bus.

    Workflow failures are tracked (Store/Draft phase).
    Approval actions only track success (Publish/Discard).
    """
    # Store phase (COMPLETE/FAIL)
    bus.subscribe(StorePhaseCompleted, handler.on_store_completed)
    bus.subscribe(StorePhaseFailed, handler.on_store_failed)

    # Draft phase (COMPLETE/FAIL)
    bus.subscribe(DraftPhaseCompleted, handler.on_draft_completed)
    bus.subscribe(DraftPhaseFailed, handler.on_draft_failed)

    # Merge phase (COMPLETE/FAIL)
    bus.subscribe(MergePhaseCompleted, handler.on_merge_completed)
    bus.subscribe(MergePhaseFailed, handler.on_merge_failed)

    # Publish (COMPLETE only - approval action)
    bus.subscribe(PublishCompleted, handler.on_publish_completed)

    # Discard (COMPLETE only - approval action)
    bus.subscribe(DiscardCompleted, handler.on_discard_completed)

    logger.info("Registered 8 lineage event handlers")
