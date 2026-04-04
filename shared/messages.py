"""WebSocket message schemas for client-server communication."""

from typing import Any, TypedDict


class JoinMessage(TypedDict):
    """Client → Server: Join a room."""

    type: str  # "join"
    name: str


class RollMessage(TypedDict):
    """Client → Server: Request a dice roll."""

    type: str  # "roll"
    expr: str
    intent: str


class EventMessage(TypedDict):
    """Server → Client: Broadcast an event."""

    type: str  # "event"
    event: dict[str, Any]


class ErrorMessage(TypedDict):
    """Server → Client: Error response."""

    type: str  # "error"
    message: str


ClientMessage = JoinMessage | RollMessage
ServerMessage = EventMessage | ErrorMessage
