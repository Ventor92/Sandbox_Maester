"""Local game service for client-side state management."""

import logging
from domain.models import Player, Room
from domain.events import RollEvent, Event
from domain.log import EventLog
from domain.dice import DiceParser

logger = logging.getLogger(__name__)


class LocalGameService:
    """Client-side game logic - manages local state and event processing."""

    def __init__(self):
        self._rooms: dict[str, Room] = {}
        self._event_logs: dict[str, EventLog] = {}
        self._local_player_id: str | None = None

    def set_local_player(self, player_id: str) -> None:
        """Set the local player ID (for tracking client's own rolls)."""
        self._local_player_id = player_id

    def get_or_create_room(self, room_id: str) -> Room:
        """Get an existing room or create a new one."""
        if room_id not in self._rooms:
            self._rooms[room_id] = Room(room_id=room_id)
            self._event_logs[room_id] = EventLog()
        return self._rooms[room_id]

    def register_player(self, room_id: str, player_name: str) -> Player | None:
        """Register a player in a room."""
        if not player_name or not player_name.strip():
            return None

        room = self.get_or_create_room(room_id)
        player = Player.create(player_name)
        room.add_player(player)
        return player

    def roll_dice(
        self, room_id: str, player_id: str, expr: str, intent: str = ""
    ) -> RollEvent | None:
        """
        Generate a local dice roll event (client-side).
        Returns: RollEvent or None if invalid.
        """
        room = self.get_or_create_room(room_id)
        player = room.get_player(player_id)

        if not player:
            return None

        dice_result = DiceParser.roll(expr)
        if not dice_result:
            return None

        event = RollEvent(
            player_id=player.client_id,
            player_name=player.name,
            dice_expr=dice_result.expr,
            rolls=dice_result.rolls,
            modifier=dice_result.modifier,
            total=dice_result.total,
            intent=intent,
        )

        log = self._event_logs[room_id]
        log.append(event)

        return event

    def process_event(self, room_id: str, event_dict: dict) -> Event | None:
        """
        Process an incoming event from server (from another client or from sync).
        Updates local state.
        """
        # Reconstruct event from dict
        if not isinstance(event_dict, dict):
            logger.warning(f"Event is not a dict: {type(event_dict)}")
            return None

        event_type = event_dict.get("type")
        if event_type != "roll":
            logger.debug(f"Skipping non-roll event type: {event_type}")
            return None

        # Extract payload structure
        payload = event_dict.get("payload", {})
        player_info = payload.get("player", {})
        dice_info = payload.get("dice", {})
        fiction_info = payload.get("fiction", {})

        player_id = player_info.get("id")
        player_name = player_info.get("name", "Unknown")
        
        if not player_id:
            logger.error(f"Missing player_id in event payload: {event_dict}")
            return None

        logger.debug(f"Processing roll event: {player_name} rolled {dice_info.get('expr')}")

        # Create event from dict
        event = RollEvent(
            player_id=player_id,
            player_name=player_name,
            dice_expr=dice_info.get("expr", ""),
            rolls=dice_info.get("rolls", []),
            modifier=dice_info.get("modifier", 0),
            total=dice_info.get("total", 0),
            intent=fiction_info.get("intent", ""),
        )

        # Add to local log and register player if needed
        room = self.get_or_create_room(room_id)
        if not room.get_player(player_id):
            new_player = Player(client_id=player_id, name=player_name)
            room.add_player(new_player)
            logger.info(f"Registered new player: {player_name} ({player_id})")

        log = self._event_logs[room_id]
        log.append(event)

        return event

    def get_recent_events(self, room_id: str, n: int = 50) -> list[Event]:
        """Get the last n events from local log."""
        if room_id not in self._event_logs:
            return []
        return self._event_logs[room_id].last(n)

    def get_all_events(self, room_id: str) -> list[Event]:
        """Get all events from local log."""
        if room_id not in self._event_logs:
            return []
        return self._event_logs[room_id].all_events()

    def get_player_count(self, room_id: str) -> int:
        """Get the number of players in local state."""
        room = self._rooms.get(room_id)
        return room.player_count() if room else 0

    def get_players(self, room_id: str) -> list[Player]:
        """Get all players in a room."""
        room = self._rooms.get(room_id)
        return room.players if room else []

    def remove_player(self, room_id: str, player_id: str) -> None:
        """Remove a player from local state."""
        room = self._rooms.get(room_id)
        if room:
            room.remove_player(player_id)
