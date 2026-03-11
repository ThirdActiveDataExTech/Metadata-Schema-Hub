"""Lineage event model for catalog-service (read-only)."""

from active_metadata.models import LineageEventBase, LineageEventType

__all__ = ["LineageEvent", "LineageEventType"]


class LineageEvent(LineageEventBase, table=True):  # type: ignore[call-arg]
    """LineageEvent table model for catalog-service (read-only)."""

    __tablename__ = "lineage_event"  # type: ignore[assignment]
