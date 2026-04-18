"""WebSocket handlers - Relay only, no game logic."""

import json
import logging
import time
from uuid import uuid4
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect
from server.room_manager import RoomManager

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handles WebSocket connections - Relay & Cache only."""

    def __init__(self, room_manager: RoomManager):
        self.room_manager = room_manager
        # Event cache: room_id → list of last N events
        self.event_cache = {}

    async def handle_connection(
        self, room_id: str, websocket: WebSocket
    ) -> None:
        """Handle a new WebSocket connection - relay and cache events."""
        client_id = None
        
        try:
            # Accept the connection first (required by WebSocket protocol)
            await websocket.accept()

            # Get JOIN message (client identifies itself)
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

            # Register client (generate ID)
            client_id = self.room_manager.register_client(room_id, websocket)
            logger.info(f"Player '{player_name}' joined room {room_id} (client: {client_id})")

            # Send cached events to new client (event history)
            cached_events = self.event_cache.get(room_id, [])
            for event_data in cached_events:
                await websocket.send_json({"type": "event", "event": event_data})

            if cached_events:
                logger.info(f"Sent {len(cached_events)} cached events to client {client_id}")

            # Send JOIN confirmation
            await websocket.send_json({
                "type": "player_joined",
                "player_name": player_name,
                "client_id": client_id
            })

            # Relay loop: receive from this client, broadcast to all in room
            while True:
                message = await websocket.receive_json()
                await self._relay_message(room_id, client_id, message)

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected from room {room_id}")
            if client_id:
                self.room_manager.disconnect(room_id, client_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if client_id:
                self.room_manager.disconnect(room_id, client_id)
            raise

    async def _relay_message(self, room_id: str, sender_id: str, message: dict[str, Any]) -> None:
        """Relay a message from client to all clients in room, cache if event."""
        msg_type = message.get("type")

        # Cache events (for late-joiners)
        if msg_type == "event":
            event_data = message.get("event", {})
            
            # Extract event details for logging from nested payload structure
            payload = event_data.get("payload", {})
            player_info = payload.get("player", {})
            dice_info = payload.get("dice", {})
            fiction_info = payload.get("fiction", {})
            
            player_name = player_info.get("name", "Unknown")
            event_type = event_data.get("type", "unknown")
            total = dice_info.get("total", 0)
            dice_expr = dice_info.get("expr", "")
            intent = fiction_info.get("intent", "")
            
            if room_id not in self.event_cache:
                self.event_cache[room_id] = []
            
            # Keep last 100 events per room
            self.event_cache[room_id].append(event_data)
            if len(self.event_cache[room_id]) > 100:
                self.event_cache[room_id] = self.event_cache[room_id][-100:]
            
            # Log the event with details
            log_msg = f"[RELAY] {player_name} rolled {dice_expr} → {total}"
            if intent:
                log_msg += f" ({intent})"
            logger.info(log_msg)
        elif msg_type == "custom_event":
            # Custom events are relayed and cached (per updated decision)
            event_data = message.get("event", {})

            # Add server-side metadata for easier consumption by clients
            meta = {
                "server_assigned_id": str(uuid4()),
                "timestamp": time.time(),
                "sender_client_id": sender_id,
            }
            if isinstance(event_data.get("metadata"), dict):
                event_data["metadata"].update(meta)
            else:
                event_data["metadata"] = meta

            if room_id not in self.event_cache:
                self.event_cache[room_id] = []

            # Keep last 100 events per room (include custom events)
            self.event_cache[room_id].append(event_data)
            if len(self.event_cache[room_id]) > 100:
                self.event_cache[room_id] = self.event_cache[room_id][-100:]

            # Log the custom event
            subtype = event_data.get("subtype", "custom")
            logger.info(f"[RELAY-CUSTOM] {sender_id} -> {room_id} ({subtype})")

        # Broadcast to all clients in room
        await self.room_manager.broadcast(room_id, message)
        logger.debug(f"Relayed {msg_type} from {sender_id} in room {room_id}")
