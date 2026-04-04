# Copilot Instructions — ttRPG Dice Roller (Event-Based)

## 🎯 Project Goal

Build a real-time ttRPG dice roller application where dice rolls are treated as **events in fiction**, not just mechanical outputs.

The system should:
- allow players to perform dice rolls
- share results in real-time
- maintain a persistent event log
- support multiple rooms (sessions)

---

## 🧭 Core Architecture Principles

### 1. Separation of Concerns (STRICT)

The project MUST be divided into clear layers:

- `domain/` → pure business logic (NO frameworks, NO IO)
- `server/` → FastAPI + WebSocket transport layer
- `client/` → Textual TUI + WebSocket client
- `shared/` → protocol definitions (JSON schemas, message formats)

**DO NOT mix these layers.**

---

### 2. Event-Driven System

- Everything is an **event**
- The system follows an **event sourcing approach**
- The event log is the **single source of truth**

---

### 3. Server Authority

- The server is authoritative
- Dice rolls MUST be executed only on the server
- Clients send only intent (never results)

---

## 🎲 Dice System (MVP Scope)

Supported formats:
- `d20`
- `2d6+1`
- `3d8-2`

Constraints:
- Validate all expressions
- Reject invalid input
- Limit number of dice (e.g. max 100)

---

## 🧾 Event Model

Each event MUST contain:

- `id` (UUID)
- `type` (string)
- `version` (int, start at 1)
- `timestamp` (float, UNIX time)
- `payload` (dict)

---

### 🎲 Roll Event

Payload structure:

```json
{
  "player": {
    "id": "uuid",
    "name": "string"
  },
  "dice": {
    "expr": "2d6+1",
    "rolls": [3, 5],
    "modifier": 1,
    "total": 9
  },
  "fiction": {
    "intent": "attack goblin"
  }
}
```

---

### ✏️ Edit Event (Future-ready)

Do NOT mutate existing events.

Instead, create new events:

```json
{
  "type": "event_edit",
  "payload": {
    "target_id": "event_id",
    "editor": "player_id",
    "changes": {}
  }
}
```

---

## 🧑‍🤝‍🧑 Players

Each player has:

* `client_id` (UUID)
* `name` (string)

No authentication system for MVP.

Future-ready:

* optional role: `"gm"` or `"player"`

---

## 🧑‍🤝‍🧑 Rooms

* Multiple rooms supported
* Each room has:

  * players
  * event log

Room is identified by `room_id` (string)

---

## 🧾 Event Log

* Append-only
* Stored in memory (MVP)
* Supports:

  * append(event)
  * last(n=50)

On reconnect:

* send last 50 events to client

---

## 🔌 WebSocket Protocol

### Client → Server

#### JOIN

```json
{
  "type": "join",
  "client_id": "...",
  "name": "..."
}
```

#### ROLL

```json
{
  "type": "roll",
  "expr": "d20",
  "intent": "attack goblin"
}
```

---

### Server → Clients

Broadcast full event:

```json
{
  "type": "event",
  "event": { ... }
}
```

---

## ⚙️ Server Behavior

On connect:

1. Accept WebSocket
2. Receive JOIN
3. Register player
4. Send last 50 events

On roll:

1. Validate expression
2. Roll dice
3. Create event
4. Append to log
5. Broadcast to all clients in room

---

## 🧠 Domain Layer (Important)

Must contain:

* `models.py` → Player, Room
* `events.py` → Event definitions
* `dice.py` → dice rolling logic
* `service.py` → GameService (use-cases)
* `log.py` → EventLog

Rules:

* NO FastAPI imports
* NO WebSocket logic
* NO UI code

---

## 🌐 Server Layer

* FastAPI app
* WebSocket endpoint: `/ws/{room_id}`
* Thin handlers only
* Delegates logic to domain service

---

## 💻 Client (Textual TUI)

Minimal UI:

* input field
* scrollable log view

Responsibilities:

* parse commands
* send JSON messages
* render incoming events

---

## 🧾 Command Parsing

Supported command:

```
/r d20 attack goblin
```

Parse into:

* `expr = "d20"`
* `intent = "attack goblin"`

---

## 🚫 Anti-Patterns (Avoid)

* Mixing domain logic with transport/UI
* Rolling dice on client
* Mutating event log directly
* Overengineering (no DB, no auth for MVP)

---

## ✅ Code Expectations

* Clean, readable Python
* Use dataclasses where appropriate
* Modular structure
* Ready for future extension

---

## 🚀 Future Extensions (Do NOT implement yet)

* GM permissions
* Hidden rolls
* Replay system
* Persistent storage
* Advanced dice mechanics (advantage, exploding dice)

---

## 🧪 Deliverable

* Working FastAPI server
* Working Textual client
* Proper project structure
* Clear separation of layers


