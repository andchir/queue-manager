#!/usr/bin/env python3
"""
Test script for verifying uvicorn WebSocket server functionality.

Tests both:
1. Traditional asyncio.run() method (python web/server.py)
2. Uvicorn ASGI method (uvicorn web.server:app)
"""

import asyncio
import json
import sys
import uuid
from websockets.asyncio.client import connect


async def test_websocket_connection(uri="ws://localhost:8765"):
    """Test basic WebSocket connection and message exchange."""
    print(f"Connecting to {uri}...")

    try:
        async with connect(uri) as websocket:
            # Receive greeting
            greeting = await websocket.recv()
            print(f"✓ Received greeting: {greeting}")
            assert "Hello from the Notification Center" in greeting

            # Register with UUID
            test_uuid = str(uuid.uuid4())
            registration_msg = json.dumps({
                "recipient_uuid": test_uuid,
                "message": "connected"
            })
            await websocket.send(registration_msg)
            print(f"✓ Registered with UUID: {test_uuid}")

            # Test sending a message (to non-existent recipient)
            test_msg = json.dumps({
                "recipient_uuid": "non-existent-uuid",
                "message": "test message"
            })
            await websocket.send(test_msg)
            print("✓ Sent test message")

            # Wait a bit to ensure server processes the message
            await asyncio.sleep(0.5)

            print("✓ All tests passed!")
            return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


async def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "8765"
    uri = f"ws://localhost:{port}"

    print("=" * 60)
    print("WebSocket Server Test")
    print("=" * 60)

    success = await test_websocket_connection(uri)

    if success:
        print("\n🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
