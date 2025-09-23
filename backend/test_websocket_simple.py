#!/usr/bin/env python3
"""
Simple WebSocket test to verify the basic functionality works.
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_simple_websocket():
    """Test the simple WebSocket endpoint."""
    uri = "ws://localhost:4003/v1/test-ws"
    
    try:
        print(f"🔌 Connecting to: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Wait for welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome)
            print(f"📥 Welcome: {welcome_data}")
            
            # Send ping
            ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            await websocket.send(json.dumps(ping_msg))
            print("📤 Sent ping")
            
            # Wait for pong
            pong = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            pong_data = json.loads(pong)
            print(f"📥 Pong: {pong_data}")
            
            # Test echo
            echo_msg = {"type": "test", "message": "Hello WebSocket!"}
            await websocket.send(json.dumps(echo_msg))
            print("📤 Sent echo test")
            
            # Wait for echo response
            echo_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            echo_data = json.loads(echo_response)
            print(f"📥 Echo: {echo_data}")
            
            print("🎉 All tests passed!")
            
    except asyncio.TimeoutError:
        print("❌ Timeout - WebSocket not responding")
    except ConnectionRefusedError:
        print("❌ Connection refused - Backend not running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket functionality...")
    asyncio.run(test_simple_websocket())
