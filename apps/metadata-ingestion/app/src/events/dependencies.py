"""FastAPI dependencies for event bus."""

from typing import Annotated

from fastapi import Depends

from app.src.events.bus import EventBus
from app.src.lineage.handler import LineageEventHandler, register_lineage_handlers
from app.src.lineage.writer import LineageWriter

__all__ = ["EventBusDep", "get_event_bus"]

# Singleton EventBus instance (shared across all requests)
_event_bus: EventBus | None = None
_initialized: bool = False


def get_lineage_writer() -> LineageWriter:
    """Get lineage writer instance (Separate TX pattern)."""
    return LineageWriter()


def get_event_bus(
    writer: Annotated[LineageWriter, Depends(get_lineage_writer)],
) -> EventBus:
    """Get event bus instance with lineage handlers registered.

    Uses singleton pattern - EventBus is created once and handlers
    are registered once on first access.
    """
    global _event_bus, _initialized

    if _event_bus is None:
        _event_bus = EventBus()

    if not _initialized:
        handler = LineageEventHandler(writer)
        register_lineage_handlers(_event_bus, handler)
        _initialized = True

    return _event_bus


EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
