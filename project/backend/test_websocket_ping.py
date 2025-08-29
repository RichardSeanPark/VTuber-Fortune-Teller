#!/usr/bin/env python3
"""Test WebSocket ping/pong functionality"""

import asyncio
import json
import websockets

async def test_ping():
    uri = "ws://localhost:8000/ws/chat/test123"
    
    async with websockets.connect(uri) as websocket:
        # First, receive connection established message
        response = await websocket.recv()
        connection_data = json.loads(response)
        print(f"Connection: {connection_data}")
        
        # Send ping message
        ping_message = {
            "type": "ping",
            "timestamp": "2025-08-22T19:40:00.000Z"
        }
        
        print(f"Sending: {ping_message}")
        await websocket.send(json.dumps(ping_message))
        
        # Wait for pong response
        response = await websocket.recv()
        response_data = json.loads(response)
        
        print(f"Received: {response_data}")
        
        if response_data.get("type") == "pong":
            print("✅ Ping-Pong test successful!")
            print(f"   Timestamp: {response_data.get('timestamp')}")
        else:
            print(f"❌ Unexpected response: {response_data}")

if __name__ == "__main__":
    asyncio.run(test_ping())