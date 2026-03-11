"""Synchronous in-process event bus.

Simple pub/sub for domain events. Handlers are called synchronously
in the same thread. Failures are logged but don't affect business logic
(best-effort pattern for lineage).
"""

import logging
from collections import defaultdict
from typing import Callable

from app.src.events.domain_events import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    """Synchronous in-process event bus with best-effort delivery."""

    def __init__(self) -> None:
        """Initialize empty handler registry."""
        self._handlers: dict[type, list[Callable[[DomainEvent], None]]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable[[DomainEvent], None]) -> None:
        """Register a handler for an event type.

        Args:
            event_type: The domain event class to subscribe to
            handler: Callable that receives the event
        """
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        """Publish event to all registered handlers.

        Handlers are called synchronously. Failures are logged but don't
        propagate (best-effort for lineage tracking).

        Args:
            event: The domain event to publish
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Best-effort: log and continue, don't affect business logic
                logger.warning(
                    f"Event handler failed for {event_type.__name__} "
                    f"(run_id={event.run_id}): {e}"
                )

    def clear(self) -> None:
        """Clear all registered handlers. Useful for testing."""
        self._handlers.clear()
