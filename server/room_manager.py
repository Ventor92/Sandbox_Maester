"""Room manager for handling WebSocket connections."""

import json
from typing import Callable
from fastapi import WebSocketException
from fastapi.websockets import WebSocket


class RoomManager:
    """Manages WebSocket connections per room and broadcasts events."""

    def __init__(self):
        # room_id -> {client_id -> WebSocket}
        self.connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, room_id: str, client_id: str, websocket: WebSocket) -> None:
        """Register a new WebSocket connection."""
        await websocket.accept()

        if room_id not in self.connections:
            self.connections[room_id] = {}

        self.connections[room_id][client_id] = websocket

    def disconnect(self, room_id: str, client_id: str) -> None:
        """Unregister a WebSocket connection."""
        if room_id in self.connections:
            self.connections[room_id].pop(client_id, None)

            if not self.connections[room_id]:
                del self.connections[room_id]

    async def broadcast(self, room_id: str, message: dict) -> None:
        """Send a message to all clients in a room."""
        if room_id not in self.connections:
            return

        disconnected = []
        for client_id, websocket in self.connections[room_id].items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(room_id, client_id)

    async def send_to_client(
        self, room_id: str, client_id: str, message: dict
    ) -> bool:
        """Send a message to a specific client."""
        if room_id not in self.connections:
            return False

        websocket = self.connections[room_id].get(client_id)
        if not websocket:
            return False

        try:
            await websocket.send_json(message)
            return True
        except Exception:
            self.disconnect(room_id, client_id)
            return False

    def get_client_count(self, room_id: str) -> int:
        """Get the number of connected clients in a room."""
        return len(self.connections.get(room_id, {}))
