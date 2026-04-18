# Custom Events (Table Rolls)

This document describes the "custom_event" message type that clients can use to relay locally-generated events (for example: results of a local "table roll") through the server to other clients in the same room.

Key points
- Clients perform the roll locally and send the result to the server as a `custom_event`.
- The server is a relay: it will *not* perform the roll or interpret the payload, but it will attach small server-side metadata and broadcast the event to all clients in the room.
- Custom events are cached in the same per-room event cache as normal events (the last 100 events) so late-joiners receive recent history.

Client → Server payload (example)

```json
{
  "type": "custom_event",
  "event": {
    "subtype": "table_roll",
    "payload": {
      "table_id": "loot",
      "choice": "sword"
    },
    "metadata": {
      "client_generated_id": "local-123"  
    }
  }
}
```

Server behaviour
- Minimal validation: `type` must be `custom_event` and `event` must be an object.
- Server will attach the following metadata under `event.metadata` (creating the key if missing):
  - `server_assigned_id` — UUID assigned by the server
  - `timestamp` — Unix time (float)
  - `sender_client_id` — the server-side client id (e.g. `client_3`)
- The enriched event is appended to the room's event cache (the same last-100 list) and then broadcast to all connected clients in the room.
- The server does not attempt to validate or interpret `payload` contents; that remains a client-side responsibility.

Server → Client broadcast (example)

```json
{
  "type": "custom_event",
  "event": {
    "subtype": "table_roll",
    "payload": {
      "table_id": "loot",
      "choice": "sword"
    },
    "metadata": {
      "client_generated_id": "local-123",
      "server_assigned_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "timestamp": 1680000000.123,
      "sender_client_id": "client_3"
    }
  }
}
```

Notes and best practices
- Keep `payload` reasonably small; very large payloads may be rejected or cause performance issues.
- If you need server-side validation of custom payloads (untrusted clients), add server-side validation in `server/handlers.py` or move logic to a domain service.
- This relay model preserves the server-as-relay principle: server only enriches and routes events, clients remain the source of truth for local logic.

Examples
- Sending a custom_event from a Textual client: use the existing WebSocket client to send the JSON above.

--

File generated to document the `custom_event` contract used by the relay server.
