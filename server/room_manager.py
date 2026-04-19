"""Room manager for handling WebSocket connections."""

from fastapi.websockets import WebSocket


class RoomManager:
    """Manages WebSocket connections per room and broadcasts events."""

    def __init__(self):
        # room_id -> {client_id -> WebSocket}
        self.connections: dict[str, dict[str, WebSocket]] = {}
        self._next_client_id = 0

    def register_client(self, room_id: str, websocket: WebSocket) -> str:
        """Register a new client and return its ID.
        
        Note: websocket MUST be already accepted before calling this.
        """
        self._next_client_id += 1
        client_id = f"client_{self._next_client_id}"
        
        if room_id not in self.connections:
            self.connections[room_id] = {}
        
        self.connections[room_id][client_id] = websocket
        return client_id

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
                import logging
                logging.debug(f"Broadcast error to {client_id}: {e}")
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(room_id, client_id)

    async def broadcast_except(self, room_id: str, exclude_client_id: str, message: dict) -> None:
        """Send a message to all clients in a room except the specified client."""
        if room_id not in self.connections:
            return

        disconnected = []
        for client_id, websocket in self.connections[room_id].items():
            if client_id == exclude_client_id:
                continue
            try:
                await websocket.send_json(message)
            except Exception as e:
                import logging
                logging.debug(f"Broadcast error to {client_id}: {e}")
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

    def list_active_rooms(self) -> list[dict[str, str | int]]:
        """Return active rooms with the number of connected clients."""
        rooms: list[dict[str, str | int]] = []

        for room_id in sorted(self.connections):
            client_count = len(self.connections[room_id])
            if client_count > 0:
                rooms.append(
                    {"room_id": room_id, "client_count": client_count}
                )

        return rooms
