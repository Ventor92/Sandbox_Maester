"""WebSocket handlers for dice roller events."""

import json
import logging
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect
from domain.service import GameService
from server.room_manager import RoomManager

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handles WebSocket connections and messages."""

    def __init__(self, room_manager: RoomManager, game_service: GameService):
        self.room_manager = room_manager
        self.game_service = game_service

    async def handle_connection(
        self, room_id: str, websocket: WebSocket
    ) -> None:
        """Handle a new WebSocket connection."""
        client_id = None

        try:
            # Accept the connection first
            await websocket.accept()

            # Wait for JOIN message
            message = await websocket.receive_json()

            if message.get("type") != "join":
                await websocket.send_json(
                    {"type": "error", "message": "First message must be JOIN"}
                )
                await websocket.close()
                return

            player_name = message.get("name", "").strip()
            if not player_name:
                await websocket.send_json(
                    {"type": "error", "message": "Player name is required"}
                )
                await websocket.close()
                return

            # Register player
            player = self.game_service.register_player(room_id, player_name)
            if not player:
                await websocket.send_json(
                    {"type": "error", "message": "Failed to register player"}
                )
                await websocket.close()
                return

            client_id = player.client_id

            # Register in connection manager (already accepted)
            self.room_manager.connections.setdefault(room_id, {})[client_id] = websocket
            logger.info(f"Player {player_name} joined room {room_id}")

            # Send recent events to the client
            recent_events = self.game_service.get_recent_events(room_id, n=50)
            for event in recent_events:
                await websocket.send_json({"type": "event", "event": event.to_dict()})

            # Handle incoming messages
            while True:
                message = await websocket.receive_json()
                await self._handle_message(room_id, client_id, message)

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected from room {room_id}")
            if client_id:
                self.room_manager.disconnect(room_id, client_id)
                self.game_service.remove_player(room_id, client_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if client_id:
                self.room_manager.disconnect(room_id, client_id)
            raise

    async def _handle_message(self, room_id: str, client_id: str, message: dict[str, Any]) -> None:
        """Process a WebSocket message."""
        msg_type = message.get("type")

        if msg_type == "roll":
            await self._handle_roll(room_id, client_id, message)
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def _handle_roll(self, room_id: str, client_id: str, message: dict[str, Any]) -> None:
        """Handle a dice roll request."""
        expr = message.get("expr", "").strip()
        intent = message.get("intent", "").strip()

        if not expr:
            await self.room_manager.send_to_client(
                room_id,
                client_id,
                {"type": "error", "message": "Dice expression is required"},
            )
            return

        # Roll on server
        event = self.game_service.roll_dice(room_id, client_id, expr, intent)

        if not event:
            await self.room_manager.send_to_client(
                room_id,
                client_id,
                {"type": "error", "message": "Invalid dice expression"},
            )
            return

        # Broadcast to all clients
        await self.room_manager.broadcast(
            room_id, {"type": "event", "event": event.to_dict()}
        )
