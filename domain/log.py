"""Event log storage."""

from typing import Any
from domain.events import Event


class EventLog:
    """Append-only event log. Events are immutable and never modified."""

    def __init__(self):
        self._events: list[Event] = []

    def append(self, event: Event) -> None:
        """Add an event to the log."""
        self._events.append(event)

    def last(self, n: int = 50) -> list[Event]:
        """Get the last n events from the log."""
        return self._events[-n:] if n > 0 else []

    def all_events(self) -> list[Event]:
        """Get all events in the log."""
        return self._events.copy()

    def size(self) -> int:
        """Get the number of events in the log."""
        return len(self._events)
