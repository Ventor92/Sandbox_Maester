"""Entry point for running the client."""

import sys
import os
import logging

# Add project root to path for textual dev mode
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.app import DiceRollerApp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dev mode defaults (for: textual run --dev client/main.py)
DEV_ROOM_ID = "dev-room"
DEV_PLAYER_NAME = "DevPlayer"
DEV_SERVER_URL = "ws://localhost:8000"


def main():
    """Run the TUI application.
    
    Usage:
        python -m client.main <room_id> <player_name> [server_url]
        
    Dev mode (no arguments required):
        python -m client.main              # Uses DEV_* defaults
        textual run --dev client/main.py   # Textual dev mode
    """
    # Check if running in dev mode (no arguments or --dev flag)
    if len(sys.argv) < 2 or sys.argv[1] in ["--dev", "-d"]:
        # Dev mode with defaults
        room_id = os.getenv("DICE_ROOM", DEV_ROOM_ID)
        player_name = os.getenv("DICE_PLAYER", DEV_PLAYER_NAME)
        server_url = os.getenv("DICE_SERVER", DEV_SERVER_URL)
        logger.info(f"🎮 Dev mode: {player_name} in {room_id} @ {server_url}")
    elif len(sys.argv) >= 3:
        # Normal mode with required arguments
        room_id = sys.argv[1]
        player_name = sys.argv[2]
        server_url = sys.argv[3] if len(sys.argv) > 3 else "ws://localhost:8000"
    else:
        # Show help
        print("Usage: python -m client.main [OPTIONS] [room_id] [player_name] [server_url]")
        print()
        print("Arguments:")
        print("  room_id      Room identifier (default: dev-room in dev mode)")
        print("  player_name  Your player name (default: DevPlayer in dev mode)")
        print("  server_url   WebSocket server URL (default: ws://localhost:8000)")
        print()
        print("Options:")
        print("  --dev, -d    Run in dev mode with defaults")
        print()
        print("Examples:")
        print("  python -m client.main                    # Dev mode (uses defaults)")
        print("  python -m client.main --dev              # Explicitly enable dev mode")
        print("  python -m client.main dungeon-01 Alice   # Normal mode")
        print("  python -m client.main room1 Bob wss://remote.com")
        print()
        print("Dev mode environment variables:")
        print("  DICE_ROOM    Override dev room ID (default: dev-room)")
        print("  DICE_PLAYER  Override dev player name (default: DevPlayer)")
        print("  DICE_SERVER  Override dev server URL (default: ws://localhost:8000)")
        print()
        print("Textual dev mode:")
        print("  textual run --dev client/main.py")
        sys.exit(1)

    app = DiceRollerApp(server_url, room_id, player_name)
    app.run()


if __name__ == "__main__":
    main()
