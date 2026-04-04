"""Quick server diagnostic - check connectivity."""

import asyncio
import subprocess
import sys


async def check_server_connectivity():
    """Check if server is accessible."""
    print("🔍 Server Connectivity Check\n")
    
    # 1. Check if server is running
    try:
        import urllib.request
        response = urllib.request.urlopen('http://localhost:8000/health', timeout=2)
        print("✓ Server is running locally")
    except Exception as e:
        print("✗ Server not running: " + str(e))
        return False
    
    # 2. Test WebSocket connection
    try:
        import websockets
        import json
        
        uri = "ws://localhost:8000/ws/test-room"
        async with websockets.connect(uri) as websocket:
            join_msg = {"type": "join", "name": "TestPlayer"}
            await websocket.send(json.dumps(join_msg))
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print("✓ WebSocket connection working")
    except Exception as e:
        print("✗ WebSocket error: " + str(e))
        return False
    
    print("\n✅ Server is ready for remote connections!")
    print("\nTo connect from another computer, use:")
    print("  python -m client.main room-1 PlayerName ws://YOUR_IP:8000")
    print("\nReplace YOUR_IP with the server's IP address (e.g., 192.168.1.16)")
    
    return True


if __name__ == "__main__":
    asyncio.run(check_server_connectivity())
