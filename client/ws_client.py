"""WebSocket client for connecting to the dice roller server."""

import asyncio
import json
import logging
from typing import Callable, Any
import websockets

logger = logging.getLogger(__name__)


class DiceRollerClient:
    """Async WebSocket client for dice roller."""

    def __init__(self, server_url: str, on_message: Callable[[dict], None]):
        self.server_url = server_url
        self.on_message = on_message
        self.websocket = None
        self.connected = False

    async def connect(self, room_id: str, player_name: str) -> bool:
        """Connect to the server and join a room."""
        try:
            # Determine protocol based on server URL
            if self.server_url.startswith("http://"):
                protocol = "ws://"
                clean_url = self.server_url.replace("http://", "")
            elif self.server_url.startswith("https://"):
                protocol = "wss://"
                clean_url = self.server_url.replace("https://", "")
            elif self.server_url.startswith("ws://") or self.server_url.startswith("wss://"):
                # Already has protocol
                url = f"{self.server_url}/ws/{room_id}"
                self.websocket = await websockets.connect(url)
            else:
                # Default to ws:// for localhost (not wss://)
                protocol = "ws://"
                clean_url = self.server_url
            
            if not self.websocket:
                url = f"{protocol}{clean_url}/ws/{room_id}"
                self.websocket = await websockets.connect(url)

            # Send JOIN message
            join_msg = {"type": "join", "name": player_name}
            await self.websocket.send(json.dumps(join_msg))

            self.connected = True
            logger.info(f"Connected to {url}")

            # Start listening for messages
            asyncio.create_task(self._listen())

            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def _listen(self) -> None:
        """Listen for incoming messages from the server."""
        try:
            while self.connected and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                self.on_message(data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Listen error: {e}")
            self.connected = False

    async def roll(self, expr: str, intent: str = "") -> None:
        """Send a roll request to the server."""
        if not self.connected or not self.websocket:
            logger.error("Not connected")
            return

        try:
            msg = {"type": "roll", "expr": expr, "intent": intent}
            await self.websocket.send(json.dumps(msg))
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def send_event(self, event_dict: dict) -> None:
        """Send an event to the server relay."""
        logger.error("Sending event to server relay")

        if not self.connected or not self.websocket:
            logger.error("Not connected")
            return

        try:
            msg = {"type": "event", "event": event_dict}
            await self.websocket.send(json.dumps(msg))
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        self.connected = False
        if self.websocket:
            await self.websocket.close()
