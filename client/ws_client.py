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

            # Fetch an auth token from the REST endpoint and include it in the JOIN
            try:
                if self.server_url.startswith("ws://"):
                    base = self.server_url.replace("ws://", "http://")
                elif self.server_url.startswith("wss://"):
                    base = self.server_url.replace("wss://", "https://")
                elif self.server_url.startswith("http://") or self.server_url.startswith("https://"):
                    base = self.server_url
                else:
                    base = f"http://{self.server_url}"

                def _fetch_token():
                    from urllib.request import urlopen
                    import json as _json
                    with urlopen(f"{base}/auth/token?room_id={room_id}&name={player_name}", timeout=2) as resp:
                        return _json.loads(resp.read().decode("utf-8")).get("token")

                token = await asyncio.get_event_loop().run_in_executor(None, _fetch_token)
                if not token:
                    logger.error("Failed to obtain auth token from server")
                    return False
            except Exception as e:
                logger.error(f"Failed to fetch auth token: {e}")
                return False

            # Send JOIN message including token
            join_msg = {"type": "join", "name": player_name, "token": token}
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
        logger.info("Sending event to server relay")

        if not self.connected or not self.websocket:
            logger.error("Not connected")
            return

        try:
            msg = {"type": "event", "event": event_dict}
            await self.websocket.send(json.dumps(msg))
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def send_custom_event(self, subtype: str, payload: dict, metadata: dict | None = None) -> None:
        """Send a custom_event message to the server."""
        if not self.connected or not self.websocket:
            logger.error("Not connected")
            return

        try:
            event = {"subtype": subtype, "payload": payload}
            if metadata:
                event["metadata"] = metadata

            msg = {"type": "custom_event", "event": event}
            await self.websocket.send(json.dumps(msg))
        except Exception as e:
            logger.error(f"Send custom event error: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        self.connected = False
        if self.websocket:
            await self.websocket.close()
