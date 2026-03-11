"""Lineage event writer with independent transaction (Separate TX pattern)."""

import logging

from sqlmodel import Session

from app.db import engine
from app.src.lineage.model import LineageEvent

__all__ = ["LineageWriter"]

logger = logging.getLogger(__name__)


class LineageWriter:
    """Write lineage events in independent transaction (best-effort).

    This implements the Separate TX pattern:
    - Creates a new session for each write operation
    - Commits independently of the business transaction
    - Failures are logged but don't affect business logic
    """

    def save(self, event: LineageEvent) -> LineageEvent | None:
        """Save event in a new independent session.

        Returns:
            The saved event with ID populated, or None on failure.
        """
        try:
            with Session(engine) as session:
                session.add(event)
                session.commit()
                session.refresh(event)
                return event
        except Exception as e:
            logger.warning(f"Lineage write failed (best-effort): {e}")
            return None
