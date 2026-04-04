#!/usr/bin/env python
"""Test with detailed event output."""

import asyncio
import json
import websockets

async def test():
    url = "sandboxmaester-production.up.railway.app"
    room = "log-test"
    
    print("[1] Alice connects...")
    ws_a = await websockets.connect(f"wss://{url}/ws/{room}")
    await ws_a.send(json.dumps({"type": "join", "name": "Alice"}))
    resp = await asyncio.wait_for(ws_a.recv(), timeout=2)
    print(f"    → {json.loads(resp).get('type')}")
    
    print("[2] Bob connects...")
    ws_b = await websockets.connect(f"wss://{url}/ws/{room}")
    await ws_b.send(json.dumps({"type": "join", "name": "Bob"}))
    resp = await asyncio.wait_for(ws_b.recv(), timeout=2)
    print(f"    → {json.loads(resp).get('type')}")
    
    print("[3] Alice rolls d20 (attack)...")
    event = {
        "type": "roll",
        "player_id": "alice",
        "player_name": "Alice",
        "dice_expr": "d20",
        "rolls": [18],
        "modifier": 0,
        "total": 18,
        "intent": "attack"
    }
    await ws_a.send(json.dumps({"type": "event", "event": event}))
    print("    → sent")
    
    print("[4] Alice rolls 2d6+1 (dodge)...")
    event2 = {
        "type": "roll",
        "player_id": "alice",
        "player_name": "Alice",
        "dice_expr": "2d6+1",
        "rolls": [3, 5],
        "modifier": 1,
        "total": 9,
        "intent": "dodge"
    }
    await ws_a.send(json.dumps({"type": "event", "event": event2}))
    print("    → sent")
    
    print("\n[5] Bob rolls 3d8 (magic)...")
    event3 = {
        "type": "roll",
        "player_id": "bob",
        "player_name": "Bob",
        "dice_expr": "3d8",
        "rolls": [7, 4, 6],
        "modifier": 0,
        "total": 17,
        "intent": "magic"
    }
    await ws_b.send(json.dumps({"type": "event", "event": event3}))
    print("    → sent")
    
    print("\n[DONE] Check Railway logs in dashboard!")
    await ws_a.close()
    await ws_b.close()

asyncio.run(test())
