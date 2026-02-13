#!/usr/bin/env python
"""
Test script to verify WebSocket server works with uvicorn.
This script starts the server and connects a test client.
"""
import asyncio
import websockets
import sys
import time


async def test_websocket_connection():
    """Test connecting to the WebSocket server and sending messages."""
    uri = "ws://localhost:8765"

    print("Connecting to WebSocket server...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")

            # Receive welcome message
            welcome = await websocket.recv()
            print(f"Received: {welcome}")

            # Send a test message with UUID
            test_uuid = "test-uuid-12345"
            message = f'{{"recipient_uuid": "{test_uuid}", "message": "connected"}}'
            print(f"Sending: {message}")
            await websocket.send(message)

            # Wait a bit
            await asyncio.sleep(1)

            # Send another test message
            message2 = f'{{"recipient_uuid": "other-uuid", "message": "Hello from test client"}}'
            print(f"Sending: {message2}")
            await websocket.send(message2)

            await asyncio.sleep(1)

            print("Test completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
