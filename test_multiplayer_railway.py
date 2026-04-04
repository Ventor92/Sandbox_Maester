#!/usr/bin/env python
"""Multi-player test on Railway - 2 clients simulating gameplay."""

import asyncio
import json
import websockets
from client.service import LocalGameService

async def simulate_player(name: str, url: str, room_id: str, rolls: list[tuple[str, str]]):
    """Simulate a player: connect, roll dice, display results."""
    service = LocalGameService()
    
    print(f"\n[{name}] Starting...")
    async with websockets.connect(f"wss://{url}/ws/{room_id}") as ws:
        # JOIN
        print(f"[{name}] Joining as {name}...")
        await ws.send(json.dumps({"type": "join", "name": name}))
        
        response = await asyncio.wait_for(ws.recv(), timeout=2)
        data = json.loads(response)
        client_id = data.get("client_id")
        print(f"[{name}] Connected (ID: {client_id[:8]}...)")
        
        # Register locally
        service.register_player(room_id, name)
        service.set_local_player(client_id)
        
        # Listen for events in background
        async def listen():
            try:
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get("type") == "event":
                        evt = data.get("event", {})
                        service.process_event(room_id, evt)
                        print(f"[{name}] Received: {evt.get('player_name')} rolled {evt.get('total')}")
                    elif data.get("type") == "player_joined":
                        other_name = data.get("player_name", "Unknown")
                        print(f"[{name}] {other_name} joined!")
            except asyncio.CancelledError:
                pass
        
        listen_task = asyncio.create_task(listen())
        
        # Perform rolls
        for expr, intent in rolls:
            await asyncio.sleep(1)  # Wait between rolls
            print(f"[{name}] Rolling {expr}...")
            
            # Roll locally
            event = service.roll_dice(room_id, client_id, expr, intent)
            if event:
                print(f"[{name}] Result: {event.total} (rolls: {event.rolls})")
                
                # Send to relay
                await ws.send(json.dumps({
                    "type": "event",
                    "event": event.to_dict()
                }))
                
                # Let other player receive it
                await asyncio.sleep(0.5)
        
        print(f"[{name}] Finished rolls")
        listen_task.cancel()
        await asyncio.sleep(1)

async def multiplayer_test():
    """Simulate 2 players on Railway."""
    url = "sandboxmaester-production.up.railway.app"
    room_id = "multiplayer-test"
    
    print("=" * 60)
    print("Multi-Player Test on Railway")
    print("=" * 60)
    
    # Alice rolls d20, 2d6, d12
    alice_rolls = [("d20", "attack"), ("2d6", "defense"), ("d12", "")]
    
    # Bob rolls d20, d10, 3d4+2
    bob_rolls = [("d20", "defense"), ("d10", "dodge"), ("3d4+2", "")]
    
    try:
        # Run both players concurrently
        await asyncio.gather(
            simulate_player("Alice", url, room_id, alice_rolls),
            simulate_player("Bob", url, room_id, bob_rolls)
        )
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Multi-player test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(multiplayer_test())
