"""Lineage event service for URI-based lineage tracking.

Note: Lineage events are created via EventBus + LineageEventHandler pattern.
This service provides read-only access to lineage events.
"""

from sqlmodel import Session

from app.src.lineage.model import LineageEvent
from app.src.lineage.repository import LineageEventRepository

__all__ = ["LineageEventService"]


class LineageEventService:
    """Service for querying lineage events (read-only).

    Note: Lineage events are written via LineageEventHandler (EventBus pattern).
    This service is for read operations only.
    """

    def __init__(self, repository: LineageEventRepository) -> None:
        """Initialize with repository."""
        self.repository = repository

    def find_events(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        job_name: str | None = None,
        event_type: str | None = None,
    ) -> list[LineageEvent]:
        """Find lineage events with optional filters."""
        return self.repository.find_all(
            db,
            limit=limit,
            offset=offset,
            job_name=job_name,
            event_type=event_type,
        )

    def find_by_ref(
        self,
        db: Session,
        ref: str,
        limit: int = 100,
    ) -> list[LineageEvent]:
        """Find events where ref is in input_refs or output_refs."""
        return self.repository.find_by_ref(db, ref, limit)
