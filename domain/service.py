"""Game service - main use-case logic."""

from domain.models import Player, Room
from domain.events import RollEvent, Event
from domain.log import EventLog
from domain.dice import DiceParser


class GameService:
    """Handles all game operations. Pure business logic, no frameworks."""

    def __init__(self):
        self._rooms: dict[str, Room] = {}
        self._event_logs: dict[str, EventLog] = {}

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
        Execute a dice roll on the server.

        Returns: RollEvent or None if player not found or expression invalid.
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

    def get_recent_events(self, room_id: str, n: int = 50) -> list[Event]:
        """Get the last n events from a room's log."""
        if room_id not in self._event_logs:
            return []
        return self._event_logs[room_id].last(n)

    def get_all_events(self, room_id: str) -> list[Event]:
        """Get all events from a room's log."""
        if room_id not in self._event_logs:
            return []
        return self._event_logs[room_id].all_events()

    def get_player_count(self, room_id: str) -> int:
        """Get the number of players in a room."""
        room = self._rooms.get(room_id)
        return room.player_count() if room else 0

    def remove_player(self, room_id: str, player_id: str) -> None:
        """Remove a player from a room."""
        room = self._rooms.get(room_id)
        if room:
            room.remove_player(player_id)
