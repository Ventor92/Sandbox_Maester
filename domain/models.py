"""Domain models for ttRPG dice roller."""

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class Player:
    """Represents a player in a game room."""

    client_id: str
    name: str

    @classmethod
    def create(cls, name: str) -> "Player":
        """Create a new player with a unique client ID."""
        return cls(client_id=str(uuid4()), name=name)


@dataclass
class Room:
    """Represents a game room/session."""

    room_id: str
    players: dict[str, Player] = field(default_factory=dict)

    def add_player(self, player: Player) -> None:
        """Add a player to the room."""
        self.players[player.client_id] = player

    def get_player(self, client_id: str) -> Player | None:
        """Get a player by client ID."""
        return self.players.get(client_id)

    def remove_player(self, client_id: str) -> None:
        """Remove a player from the room."""
        self.players.pop(client_id, None)

    def player_count(self) -> int:
        """Get the number of players in the room."""
        return len(self.players)
