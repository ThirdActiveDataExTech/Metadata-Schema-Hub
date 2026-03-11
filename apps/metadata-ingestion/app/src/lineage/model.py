"""Lineage event model for metadata-ingestion service."""

from active_metadata.models import LineageEventBase

__all__ = ["LineageEvent"]


class LineageEvent(LineageEventBase, table=True):  # type: ignore[call-arg]
    """LineageEvent table model for metadata-ingestion."""

    __tablename__ = "lineage_event"  # type: ignore[assignment]
