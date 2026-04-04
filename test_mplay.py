#!/usr/bin/env python
"""Test Railway multi-player with simple event sync."""

import asyncio
import json
import websockets

async def test_multiplayer_railway():
    """Test that Alice's event reaches Bob."""
    url = "sandboxmaester-production.up.railway.app"
    room_id = "mtest"
    
    print("[TEST] Railway Multi-Player Relay")
    print("=" * 50)
    
    # Alice connects
    print("\n[Alice] Connecting...")
    ws_a = await websockets.connect(f"wss://{url}/ws/{room_id}")
    await ws_a.send(json.dumps({"type": "join", "name": "Alice"}))
    msg = await asyncio.wait_for(ws_a.recv(), timeout=2)
    print(f"[Alice] Joined: {json.loads(msg).get('type')}")
    
    # Bob connects
    print("\n[Bob] Connecting...")
    ws_b = await websockets.connect(f"wss://{url}/ws/{room_id}")
    await ws_b.send(json.dumps({"type": "join", "name": "Bob"}))
    msg = await asyncio.wait_for(ws_b.recv(), timeout=2)
    print(f"[Bob] Joined: {json.loads(msg).get('type')}")
    
    # Alice rolls d20
    print("\n[Alice] Rolling d20...")
    event = {
        "type": "roll",
        "player_id": "alice_id",
        "player_name": "Alice",
        "dice_expr": "d20",
        "rolls": [15],
        "modifier": 0,
        "total": 15,
        "intent": "attack"
    }
    await ws_a.send(json.dumps({"type": "event", "event": event}))
    print("[Alice] Event sent")
    
    # Bob waits for Alice's event via relay
    print("\n[Bob] Waiting for Alice's roll...")
    try:
        msg = await asyncio.wait_for(ws_b.recv(), timeout=2)
        data = json.loads(msg)
        if data.get("type") == "event":
            evt = data.get("event", {})
            print(f"[Bob] Received: {evt.get('player_name')} rolled {evt.get('total')}")
            print("\n[SUCCESS] Relay working!")
        else:
            print(f"[Bob] Wrong type: {data.get('type')}")
    except asyncio.TimeoutError:
        print("[Bob] TIMEOUT - no relay!")
    
    # Alice receives her own broadcast
    print("\n[Alice] Waiting for broadcast...")
    try:
        msg = await asyncio.wait_for(ws_a.recv(), timeout=1)
        data = json.loads(msg)
        print(f"[Alice] Broadcast: {data.get('type')}")
    except asyncio.TimeoutError:
        print("[Alice] No broadcast received")
    
    await ws_a.close()
    await ws_b.close()
    print("\n[DONE]")

if __name__ == "__main__":
    asyncio.run(test_multiplayer_railway())
