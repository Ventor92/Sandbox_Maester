# Copilot Instructions — ttRPG Dice Roller (Relay + Client State)

## 🎯 Project Goal

Build a real-time tabletop RPG dice roller that supports multiplayer sessions. The system uses a **relay server architecture** (stateless) with **client-side state management**, enabling horizontal scaling on stateless hosting services like Railway.

---

## 🧭 Architecture Overview

### Relay + Client State Model

```
┌─────────────┐                  ┌──────────────┐
│   Client    │◄─ WebSocket ─►   │   Server     │
│  (TUI)      │  (relay only)     │  (relay)     │
│  +State     │                   │  +cache      │
│  +Logic     │                   │              │
└─────────────┘                  └──────────────┘
  └─ Local GameService            └─ Pure relay
    └─ Event log                     └─ Last 100 events per room
    └─ Dice rolls
    └─ Validation
```

### Key Principle: Stateless Server

- ✅ Server is a **pure relay** (no game logic)
- ✅ No GameService dependency on server
- ✅ Caches last 100 events per room for late-joiners
- ✅ Can run multiple instances without coordination
- ✅ Client is **fully responsible** for its state and event generation

---

## 📁 Strict Layer Separation

| Layer | Responsibility | Framework | Key Files |
|-------|---|---|---|
| **Domain** | Pure business logic (pure Python) | None | `domain/models.py`, `domain/dice.py`, `domain/events.py`, `domain/log.py`, `domain/service.py` |
| **Server** | WebSocket relay + event caching | FastAPI | `server/app.py`, `server/handlers.py`, `server/room_manager.py`, `server/main.py` |
| **Client** | TUI + local GameService + WebSocket client | Textual | `client/app.py`, `client/service.py`, `client/ws_client.py`, `client/parser.py`, `client/renderer.py`, `client/main.py` |
| **Shared** | Protocol definitions | Pydantic | `shared/messages.py` |

**CRITICAL**: 
- Domain layer has NO FastAPI, NO WebSocket, NO UI imports
- Server layer has NO game logic (only relay)
- Client has a LOCAL copy of GameService (`client/service.py`)

---

## 🎲 Dice System

Supported formats:
- `d20` → roll 1d20
- `2d6+1` → roll 2d6 plus 1 modifier
- `3d8-2` → roll 3d8 minus 2 modifier

Validation in `domain/dice.py`:
- Uses regex to parse expressions
- Rejects invalid syntax
- Limits dice count (max 100)
- Returns `DiceResult` with rolls, modifier, total

---

## 🧾 Event Model

All state changes are immutable events (frozen dataclasses):

```python
@dataclass(frozen=True)
class RollEvent:
    id: str              # UUID
    type: str            # "roll"
    version: int         # 1
    timestamp: float     # Unix time
    payload: dict        # See below
```

Event payload structure:
```python
{
    "player_name": "Alice",
    "dice_expr": "d20",
    "rolls": [15],
    "modifier": 0,
    "total": 15,
    "intent": "attack goblin"
}
```

---

## 🔌 WebSocket Protocol

### Client → Server

```json
{"type": "join", "name": "Alice"}
{"type": "event", "event": {...}}
```

### Server → Client

```json
{"type": "event", "event": {...}}
{"type": "player_joined", "player_name": "Alice", "client_id": "client_1"}
{"type": "error", "message": "Invalid expression"}
```

---

## 🚀 Running the Application

### Prerequisites
```bash
python -m pip install -r requirements.txt
```

### Start Server
```bash
python -m server.main
```
Runs on `http://localhost:8000`. Health check: `http://localhost:8000/health`

### Start Clients
```bash
python -m client.main <room_id> <player_name> [server_url]
```

Examples:
```bash
python -m client.main dungeon-01 Alice                                    # Local
python -m client.main dungeon-01 Bob ws://192.168.1.16:8000             # LAN
python -m client.main dungeon-01 Alice wss://sandboxmaester-prod.up...  # Remote
```

### Docker
```bash
docker-compose up  # Starts server + 2 clients
```

---

## 🧪 Testing

The codebase includes test files (not a full pytest suite):

- `test_websocket.py` — Low-level WebSocket connectivity
- `test_logging.py` — Event logging via relay
- `test_local_relay.py` — Local server relay behavior
- `test_complete_relay.py` — Full flow (join → roll → broadcast)
- `test_railway_health.py` — Production health check
- `test_multiplayer_railway.py` — Production multiplayer test

Run with:
```bash
python test_logging.py
python test_complete_relay.py
```

**Note**: No pytest/unittest framework. Tests are standalone async scripts using `asyncio` + `websockets`.

---

## 🔄 Client State Flow

### 1. Connection & Initialization
```
Client → Server: {"type": "join", "name": "Alice"}
Server → Client: 
  - Last 100 events (to sync state)
  - {"type": "player_joined", "player_name": "Alice", "client_id": "client_1"}
Client: Initialize LocalGameService, process cached events
```

### 2. Rolling Dice
```
User types: /r d20 attack
Client:
  1. Parse command → expr="d20", intent="attack"
  2. Generate event via LocalGameService.roll_dice()
  3. Send event to server
  4. Display immediately (optimistic update)
  5. Receive own event back from broadcast
```

### 3. Other Players' Rolls
```
Server: Receives event from Alice → broadcasts to all clients
Client (Bob):
  1. Receives event via WebSocket
  2. Processes in LocalGameService
  3. Renderer formats for display
  4. TUI updates
```

---

## 📝 Key Code Patterns

### Server: Pure Relay
```python
# handlers.py - NO game logic here
async def handle_connection(room_id: str, websocket: WebSocket):
    await websocket.accept()
    
    # GET JOIN MESSAGE
    message = await websocket.receive_json()
    client_id = self.room_manager.register_client(room_id, websocket)
    
    # SEND CACHED EVENTS
    cached = self.event_cache.get(room_id, [])
    for event in cached:
        await websocket.send_json({"type": "event", "event": event})
    
    # RELAY LOOP
    while True:
        message = await websocket.receive_json()
        
        # Cache if event, then broadcast
        if message.get("type") == "event":
            self.event_cache[room_id].append(message["event"])
        
        await self.room_manager.broadcast(room_id, message)
```

### Client: Local Authority
```python
# client/app.py
def on_roll_command(self, expr: str, intent: str):
    # Generate event locally
    event = self.service.roll_dice(expr, intent)
    
    # Send to relay
    await self.ws_client.send_event(event)
    
    # Display immediately (don't wait for echo)
    self.render_event(event)
```

### Domain: Framework-Agnostic
```python
# domain/service.py - Can run anywhere
class GameService:
    def roll_dice(self, expr: str, intent: str) -> RollEvent:
        dice_result = DiceParser.roll(expr)  # Pure function
        if not dice_result:
            raise ValueError("Invalid expression")
        
        return RollEvent(
            id=str(uuid4()),
            type="roll",
            timestamp=time.time(),
            payload={...}
        )
```

---

## ⚠️ Critical Gotchas

### WebSocket Connection
- **ALWAYS call `websocket.accept()`** before sending/receiving
- Register client AFTER accepting
- If broadcast fails, disconnect that client
- See `room_manager.py:broadcast()` for error handling pattern

### Event Caching
- Keep last 100 events per room (see `handlers.py` line 102)
- Cache BEFORE broadcasting (ensures late-joiners get it)
- Clear cache when room becomes empty (optional optimization)

### Client-Side Validation
- Dice parser validates expressions before sending
- Server relay doesn't validate (assumes client is trusted)
- If attacking untrusted clients: validate on server too

### Local vs. Remote URLs
- Local: `ws://localhost:8000` or `ws://127.0.0.1:8000`
- LAN: `ws://192.168.x.x:8000`
- Remote: `wss://domain.com` (Railway auto-upgrades to wss://)
- See `test_websocket.py` for protocol detection logic

---

## 🚫 Anti-Patterns

- ❌ Server generating events (except JOIN confirmation)
- ❌ Mutating events after creation
- ❌ Keeping state on server between requests
- ❌ Rolling dice without validation

---

## 🔮 Future Extensions

1. **Persistence**: Add database to store event log permanently
2. **Offline Support**: Queue events locally, sync on reconnect
3. **Conflict Resolution**: Handle out-of-order events via event versioning
4. **Client Validation**: Pre-validate expressions before sending
5. **Compression**: Gzip large event caches
6. **GM Features**: Permissions, hidden rolls, spell/ability management

**When adding features:**
- Add logic to BOTH `domain/` and `client/service.py` (if logic, not relay)
- Keep server relay minimal
- Maintain protocol backward compatibility

---

## 📚 Reference Documents

- **Architecture**: `ARCHITECTURE_V2.md` — Detailed v1→v2 migration
- **Deployment**: `DOCKER_GUIDE.md`, `DOCKER_QUICK_START.md`
- **Networking**: `NETWORK_GUIDE.md` — LAN/remote setup
- **Implementation**: `IMPLEMENTATION_SUMMARY.md` — What was built
