#!/usr/bin/env python3
"""
Test script for session WebSocket endpoint
"""
import asyncio
import websockets
import json
import datetime

async def test_session_websocket():
    """Test the session WebSocket endpoint"""
    print("🧪 Testing Session WebSocket functionality...")
    
    # Test session ID
    session_id = "test_session_123"
    ws_url = f"ws://localhost:4003/v1/sessions/{session_id}/ws"
    
    try:
        print(f"🔌 Connecting to: {ws_url}")
        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected successfully!")
            
            # Wait for connection established message
            print("📥 Waiting for connection message...")
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Connection: {data}")
            
            # Send a ping
            print("📤 Sending ping...")
            ping_msg = {"type": "ping", "timestamp": datetime.datetime.now().isoformat()}
            await websocket.send(json.dumps(ping_msg))
            
            # Wait for pong
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 Pong: {data}")
            
            # Send a test message
            print("📤 Sending test message...")
            message = {
                "type": "message",
                "content": "Hello, this is a test message!",
                "user_id": "vivek_001",
                "referenced_product_ids": []
            }
            await websocket.send(json.dumps(message))
            
            # Wait for responses
            print("📥 Waiting for message responses...")
            for i in range(5):  # Wait for up to 5 responses
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    print(f"📥 Response {i+1}: {data}")
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout waiting for response {i+1}")
                    break
            
            print("🎉 Session WebSocket test completed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_session_websocket())
