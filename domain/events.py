"""Event model and definitions."""

from dataclasses import dataclass, field
from uuid import uuid4
import time
from typing import Any


@dataclass(frozen=True)
class Event:
    """Base event structure. Events are immutable."""

    id: str = field(default_factory=lambda: str(uuid4()))
    type: str = ""
    version: int = 1
    timestamp: float = field(default_factory=time.time)
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "version": self.version,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class RollEvent(Event):
    """Event representing a dice roll."""

    def __init__(
        self,
        player_id: str,
        player_name: str,
        dice_expr: str,
        rolls: list[int],
        modifier: int,
        total: int,
        intent: str = "",
    ):
        object.__setattr__(self, "id", str(uuid4()))
        object.__setattr__(self, "type", "roll")
        object.__setattr__(self, "version", 1)
        object.__setattr__(self, "timestamp", time.time())
        object.__setattr__(
            self,
            "payload",
            {
                "player": {"id": player_id, "name": player_name},
                "dice": {
                    "expr": dice_expr,
                    "rolls": rolls,
                    "modifier": modifier,
                    "total": total,
                },
                "fiction": {"intent": intent},
            },
        )
