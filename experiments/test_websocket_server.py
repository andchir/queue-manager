#!/usr/bin/env python
"""
Integration test for WebSocket server with websockets 16.0 asyncio API.
This test verifies that the server works correctly after migration from legacy API.
"""

import sys
import os
import asyncio
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from websockets.asyncio.client import connect


async def test_server_connection(port=8766):
    """Test basic server connection and greeting."""
    uri = f'ws://localhost:{port}'

    try:
        async with connect(uri) as websocket:
            # Should receive greeting message
            greeting = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"Received greeting: {greeting}")
            assert "Hello from the Notification Center" in greeting, f"Unexpected greeting: {greeting}"
            print("✓ Greeting test passed")

            # Test sending a message with UUID registration
            connect_msg = json.dumps({'recipient_uuid': 'test-client-1', 'message': 'connected'})
            await websocket.send(connect_msg)
            print(f"✓ UUID registration message sent")

            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_message_forwarding(port=8766):
    """Test message forwarding between two clients."""
    uri = f'ws://localhost:{port}'

    try:
        # Connect first client (receiver)
        async with connect(uri) as receiver:
            # Skip greeting
            await receiver.recv()

            # Register receiver with UUID
            await receiver.send(json.dumps({'recipient_uuid': 'receiver-uuid', 'message': 'connected'}))

            # Connect second client (sender)
            async with connect(uri) as sender:
                # Skip greeting
                await sender.recv()

                # Send message to receiver
                test_message = "Hello from sender!"
                await sender.send(json.dumps({
                    'recipient_uuid': 'receiver-uuid',
                    'message': test_message
                }))

                # Receiver should get the message
                received = await asyncio.wait_for(receiver.recv(), timeout=5.0)
                assert received == test_message, f"Expected '{test_message}', got '{received}'"
                print(f"✓ Message forwarding test passed: received '{received}'")

                return True
    except Exception as e:
        print(f"✗ Error in message forwarding: {e}")
        return False


async def run_server_and_tests():
    """Run the server and tests together."""
    from web.server import register
    from websockets.asyncio.server import serve

    port = 8766

    # Start server
    async with serve(register, host='localhost', port=port, ping_interval=60, ping_timeout=30):
        print(f"Server started on port {port}")

        # Run tests
        test1_passed = await test_server_connection(port)
        test2_passed = await test_message_forwarding(port)

        if test1_passed and test2_passed:
            print("\n✓ All tests passed!")
            return True
        else:
            print("\n✗ Some tests failed")
            return False


if __name__ == "__main__":
    success = asyncio.run(run_server_and_tests())
    sys.exit(0 if success else 1)
