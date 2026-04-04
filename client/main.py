"""Entry point for running the client."""

import sys
import logging

from client.app import DiceRollerApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run the TUI application."""
    if len(sys.argv) < 3:
        print("Usage: python -m client.main <room_id> <player_name> [server_url]")
        print("Example: python -m client.main dungeon-01 Alice ws://localhost:8000")
        sys.exit(1)

    room_id = sys.argv[1]
    player_name = sys.argv[2]
    server_url = sys.argv[3] if len(sys.argv) > 3 else "ws://localhost:8000"

    app = DiceRollerApp(server_url, room_id, player_name)
    app.run()


if __name__ == "__main__":
    main()
