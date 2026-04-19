# ttRPG Dice Roller - Implementation Complete

A real-time tabletop RPG dice roller with event-based architecture.

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Quick Start with Docker

```bash
# Start everything with one command (requires Docker)
docker-compose up
```

This starts:
- Server on http://localhost:8000
- Client (Alice) - ready to roll
- Client (Bob) - ready to roll
- All connected and playing!

See **DOCKER_QUICK_START.md** for Docker commands.

### Running the Application

#### Terminal 1: Start the Server

```bash
python -m server.main
```

The server will start on `http://localhost:8000`. Check health at `http://localhost:8000/health` and active rooms at `http://localhost:8000/rooms`.

#### Terminal 2 & 3: Start Clients (Local)

```bash
python -m client.main <room_id> <player_name>
```

Examples:
```bash
python -m client.main dungeon-01 Alice
python -m client.main dungeon-01 Bob
```

#### Remote Clients (Different Computer)

First, find the server's IP address:
```bash
# On Windows
ipconfig

# On Linux/Mac
ifconfig
```

Then connect from another computer:
```bash
python -m client.main <room_id> <player_name> ws://<server_ip>:8000
```

Example (server at 192.168.1.16):
```bash
python -m client.main dungeon-01 Alice ws://192.168.1.16:8000
```

### Usage

In the client TUI:

```
/r d20                    - Roll a d20
/r 2d6+1                  - Roll 2d6 with +1 modifier
/r 3d8-2 attack goblin    - Roll 3d8-2 with intent text
```

## Project Structure

```
domain/                 # Pure business logic (NO frameworks)
├── models.py          # Player, Room dataclasses
├── events.py          # Event definitions (immutable)
├── dice.py            # Dice parser and roller
├── log.py             # Append-only event log
└── service.py         # GameService (use-cases)

server/                 # FastAPI + WebSocket transport
├── app.py             # FastAPI application
├── handlers.py        # WebSocket message handlers
├── room_manager.py    # Connection management & broadcasting
└── main.py            # Server entry point

client/                 # Textual TUI interface
├── app.py             # TUI application
├── ws_client.py       # WebSocket client
├── parser.py          # Command parser
├── renderer.py        # Event rendering
└── main.py            # Client entry point

shared/                 # Shared definitions
└── messages.py        # WebSocket message schemas
```

## Architecture

### Separation of Concerns

- **Domain Layer**: Pure Python business logic with NO external framework imports
  - Validates dice expressions (d20, 2d6+1, 3d8-2)
  - Provides pure models and functions usable by client and server
  - Keeps domain logic framework-agnostic (no WebSocket/FastAPI imports)

- **Server Layer**: FastAPI + WebSocket transport
  - Accepts WebSocket connections
  - Validates incoming messages (pydantic)
  - Relays messages and enriches events with metadata; does not perform game logic
  - Broadcasts events to all clients in room

- **Client Layer**: Textual TUI
  - Parses commands (/r d20 intent)
  - Sends requests via WebSocket
  - Renders events in real-time

### Event Model

All game state changes are represented as immutable events:

```json
{
  "id": "uuid",
  "type": "roll",
  "version": 1,
  "timestamp": 1234567890.0,
  "payload": {
    "player": { "id": "uuid", "name": "Alice" },
    "dice": {
      "expr": "d20",
      "rolls": [15],
      "modifier": 0,
      "total": 15
    },
    "fiction": { "intent": "attack" }
  }
}
```

## WebSocket Protocol

### Client → Server

```json
{ "type": "join", "name": "Alice" }
{ "type": "roll", "expr": "d20", "intent": "attack" }
```

Note: A short-lived JWT token must be obtained from `/auth/token` and included as a query parameter (`?token=<JWT>`) on the WebSocket URL during the handshake. The server verifies the token before accepting the connection.

### Server → Client

```json
{ "type": "event", "event": { ... } }
{ "type": "error", "message": "Invalid dice expression" }
```

## MVP Features

- ✅ Multiple rooms (sessions)
- ✅ Real-time event broadcasting (relay)
- ✅ Dice expression validation
- ✅ Client-side dice rolls (clients generate roll events)
- ✅ Persistent event log during session (in-memory)
- ✅ Last 100 events sent on reconnect
- ✅ Command-based TUI interface

## Future Extensions (Not Implemented)

- GM permissions and hidden rolls
- Persistent storage (database)
- User authentication
- Advanced dice mechanics (advantage, exploding dice)
- Event replay system
- Discord/Slack integration

## Development Notes

- **No Database**: Event log is in-memory for MVP
- **Authentication**: Short-lived JWT tokens are issued for WS handshake (MVP)
- **Server role**: Server is a relay only (does not perform game logic); clients are local authority and may generate dice rolls
- **Framework-Agnostic Domain**: Domain layer can be reused across transports (client or server)

## Testing

The application was built for functionality. To extend with tests:

```bash
# Domain layer tests
pytest tests/test_domain/ -v

# Server layer tests (WebSocket mocking)
pytest tests/test_server/ -v

# Client layer tests
pytest tests/test_client/ -v
```

## Troubleshooting

### "Connection refused" on client
- Verify server is running: `python -m server.main`
- Check server is on localhost:8000
- For remote connections, use correct server IP: `ws://192.168.1.16:8000`

### "Cannot connect from another computer"
- Ensure server is listening on all interfaces (it is: `0.0.0.0:8000`)
- Check firewall allows port 8000
- Use server's IP address, not 127.0.0.1 (which is localhost only)
- On Windows, open port: `netsh advfirewall firewall add rule name="Dice Roller" dir=in action=allow protocol=tcp localport=8000`

### "Invalid dice expression"
- Check syntax: d20, 2d6+1, 3d8-2
- No spaces in dice expression

### Client freezes
- Textual TUI may need terminal resizing
- Ctrl+C to quit

### "timed out" on WebSocket
- Server may not be running
- Check health endpoint: `curl http://localhost:8000/health`
- Network connectivity issue

## Remote Networking

### Local Area Network (LAN)
```bash
# Find server IP (e.g., 192.168.1.16)
# Client connects with: ws://192.168.1.16:8000
python -m client.main room-1 Alice ws://192.168.1.16:8000
```

### Firewall Rules
- Windows: Allow port 8000 inbound
- Linux: `sudo ufw allow 8000/tcp`
- macOS: System Preferences > Security & Privacy

### SSH Tunnel (Remote Access)
```bash
# From client machine
ssh -L 8000:localhost:8000 user@server_machine
python -m client.main room-1 Alice ws://localhost:8000
```

## License

MIT
