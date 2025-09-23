#!/usr/bin/env python3
"""
Test script to verify WebSocket functionality.
Run this after installing dependencies to test WebSocket support.
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_connection():
    """Test WebSocket connection to the backend."""
    # Test the simple test endpoint first
    uri = "ws://localhost:4003/v1/test-ws"
    
    try:
        print(f"Connecting to WebSocket: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established!")
            
            # Wait for welcome message
            welcome_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome_response)
            print(f"📥 Received welcome: {welcome_data}")
            
            if welcome_data.get("type") == "welcome":
                print("✅ WebSocket welcome message received!")
            
            # Send a ping message
            ping_message = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping message")
            
            # Wait for pong response
            pong_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            pong_data = json.loads(pong_response)
            print(f"📥 Received pong: {pong_data}")
            
            if pong_data.get("type") == "pong":
                print("✅ WebSocket ping/pong test successful!")
            else:
                print("⚠️  Unexpected response type")
                
            # Test echo functionality
            echo_message = {
                "type": "test",
                "message": "Hello WebSocket!",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(echo_message))
            print("📤 Sent echo test message")
            
            # Wait for echo response
            echo_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            echo_data = json.loads(echo_response)
            print(f"📥 Received echo: {echo_data}")
            
            if echo_data.get("type") == "echo":
                print("✅ WebSocket echo test successful!")
            else:
                print("⚠️  Unexpected echo response type")
                
    except asyncio.TimeoutError:
        print("❌ WebSocket connection timeout")
    except ConnectionRefusedError:
        print("❌ WebSocket connection refused - make sure the backend is running")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    print("Testing WebSocket functionality...")
    asyncio.run(test_websocket_connection())
