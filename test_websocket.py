#!/usr/bin/env python
"""Simple WebSocket test client - ping pong without full app."""

import asyncio
import json
import sys
import websockets

async def test_websocket(server_url: str, room_id: str = "test-room"):
    """Connect to WebSocket and send ping."""
    try:
        # Determine protocol
        if server_url.startswith("http://"):
            protocol = "ws://"
            clean_url = server_url.replace("http://", "")
        elif server_url.startswith("https://"):
            protocol = "wss://"
            clean_url = server_url.replace("https://", "")
        else:
            # Default to wss:// for Railway (no protocol specified)
            protocol = "wss://"
            clean_url = server_url
        url = f"{protocol}{clean_url}/ws/{room_id}"
        
        print(f"📡 Connecting to: {url}")
        
        async with websockets.connect(url) as ws:
            print("✅ WebSocket connected!")
            
            # Send JOIN
            join_msg = {"type": "join", "name": "TestClient"}
            print(f"📤 Sending: {join_msg}")
            await ws.send(json.dumps(join_msg))
            
            # Listen for responses
            print("📥 Waiting for server responses (10 seconds)...")
            try:
                msg_count = 0
                for i in range(10):
                    response = await asyncio.wait_for(ws.recv(), timeout=1)
                    msg_count += 1
                    data = json.loads(response)
                    print(f"  [{msg_count}] {data}")
                
                if msg_count == 0:
                    print("⏱️  No messages received")
                else:
                    print(f"✅ Received {msg_count} messages")
                    
            except asyncio.TimeoutError:
                if msg_count > 0:
                    print(f"✅ Received {msg_count} messages total")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_websocket.py <server_url> [room_id]")
        print("Example: python test_websocket.py sandboxmaester-production.up.railway.app")
        print("Example: python test_websocket.py localhost:8000")
        sys.exit(1)
    
    server_url = sys.argv[1]
    room_id = sys.argv[2] if len(sys.argv) > 2 else "test-room"
    
    asyncio.run(test_websocket(server_url, room_id))
