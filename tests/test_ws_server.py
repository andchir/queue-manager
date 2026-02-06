"""
Tests for web/server.py
Testing WebSocket server connection management, message parsing, and cleanup logic.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web.server import (
    WebSocketMessage,
    _add_connection,
    _remove_connection_by_key,
    _remove_connection_by_ws,
    _parse_message,
    CONNECTIONS,
    WS_TO_KEY,
)


class TestWebSocketMessage(unittest.TestCase):
    """Test WebSocketMessage dataclass."""

    def test_default_values(self):
        msg = WebSocketMessage()
        self.assertIsNone(msg.recipient_uuid)
        self.assertIsNone(msg.message)

    def test_with_values(self):
        msg = WebSocketMessage(recipient_uuid='abc-123', message='hello')
        self.assertEqual(msg.recipient_uuid, 'abc-123')
        self.assertEqual(msg.message, 'hello')


class TestParseMessage(unittest.TestCase):
    """Test _parse_message function."""

    def test_plain_text_message(self):
        result = _parse_message('hello world')
        self.assertIsInstance(result, WebSocketMessage)
        self.assertEqual(result.message, 'hello world')
        self.assertIsNone(result.recipient_uuid)

    def test_json_message_with_recipient(self):
        msg = json.dumps({'recipient_uuid': 'abc-123', 'message': 'hello'})
        result = _parse_message(msg)
        self.assertIsInstance(result, WebSocketMessage)
        self.assertEqual(result.recipient_uuid, 'abc-123')
        self.assertEqual(result.message, 'hello')

    def test_json_connected_message(self):
        msg = json.dumps({'recipient_uuid': 'user-uuid', 'message': 'connected'})
        result = _parse_message(msg)
        self.assertEqual(result.recipient_uuid, 'user-uuid')
        self.assertEqual(result.message, 'connected')

    def test_invalid_json_starting_with_brace(self):
        with self.assertRaises(json.JSONDecodeError):
            _parse_message('{invalid json}')

    def test_json_message_with_only_message(self):
        msg = json.dumps({'message': 'test'})
        result = _parse_message(msg)
        self.assertIsNone(result.recipient_uuid)
        self.assertEqual(result.message, 'test')

    def test_json_array_falls_back_to_plain(self):
        """JSON array (not dict) should be treated as plain message."""
        msg = '["not", "a", "dict"]'
        # Does not start with '{', so treated as plain text
        result = _parse_message(msg)
        self.assertEqual(result.message, msg)


class TestConnectionManagement(unittest.TestCase):
    """Test connection add/remove helper functions."""

    def setUp(self):
        CONNECTIONS.clear()
        WS_TO_KEY.clear()

    def tearDown(self):
        CONNECTIONS.clear()
        WS_TO_KEY.clear()

    def test_add_connection(self):
        ws = MagicMock()
        _add_connection('key1', ws)
        self.assertIn('key1', CONNECTIONS)
        self.assertEqual(CONNECTIONS['key1'], ws)
        self.assertIn(id(ws), WS_TO_KEY)
        self.assertEqual(WS_TO_KEY[id(ws)], 'key1')

    def test_remove_connection_by_key(self):
        ws = MagicMock()
        _add_connection('key1', ws)
        _remove_connection_by_key('key1')
        self.assertNotIn('key1', CONNECTIONS)
        self.assertNotIn(id(ws), WS_TO_KEY)

    def test_remove_connection_by_key_nonexistent(self):
        """Removing a nonexistent key should not raise."""
        _remove_connection_by_key('nonexistent')

    def test_remove_connection_by_ws(self):
        ws = MagicMock()
        _add_connection('key1', ws)
        _remove_connection_by_ws(ws)
        self.assertNotIn('key1', CONNECTIONS)
        self.assertNotIn(id(ws), WS_TO_KEY)

    def test_remove_connection_by_ws_nonexistent(self):
        """Removing a nonexistent websocket should not raise."""
        ws = MagicMock()
        _remove_connection_by_ws(ws)

    def test_add_replaces_existing_key(self):
        """Adding a new websocket for the same key replaces the old one."""
        ws1 = MagicMock()
        ws2 = MagicMock()
        _add_connection('key1', ws1)
        _add_connection('key1', ws2)
        self.assertEqual(CONNECTIONS['key1'], ws2)
        self.assertEqual(WS_TO_KEY[id(ws2)], 'key1')

    def test_uuid_reassignment(self):
        """Simulate the flow: tmp connection -> UUID assignment."""
        ws = MagicMock()
        tmp_key = 'tmp_abc123'
        real_key = 'user-uuid-456'

        # Initial connection
        _add_connection(tmp_key, ws)
        self.assertIn(tmp_key, CONNECTIONS)

        # UUID assignment
        _remove_connection_by_key(tmp_key)
        _add_connection(real_key, ws)

        self.assertNotIn(tmp_key, CONNECTIONS)
        self.assertIn(real_key, CONNECTIONS)
        self.assertEqual(WS_TO_KEY[id(ws)], real_key)

    def test_multiple_connections(self):
        """Multiple connections should be tracked independently."""
        ws1 = MagicMock()
        ws2 = MagicMock()
        ws3 = MagicMock()

        _add_connection('key1', ws1)
        _add_connection('key2', ws2)
        _add_connection('key3', ws3)

        self.assertEqual(len(CONNECTIONS), 3)
        self.assertEqual(len(WS_TO_KEY), 3)

        _remove_connection_by_ws(ws2)
        self.assertEqual(len(CONNECTIONS), 2)
        self.assertNotIn('key2', CONNECTIONS)
        self.assertIn('key1', CONNECTIONS)
        self.assertIn('key3', CONNECTIONS)

    def test_cleanup_after_disconnect_uses_reverse_lookup(self):
        """Verify that disconnect cleanup is O(1) via reverse lookup, not O(n) scan."""
        ws = MagicMock()
        _add_connection('user-uuid', ws)

        # The reverse lookup should find the key directly
        key = WS_TO_KEY.get(id(ws))
        self.assertEqual(key, 'user-uuid')

        # Cleanup should work via _remove_connection_by_ws
        _remove_connection_by_ws(ws)
        self.assertEqual(len(CONNECTIONS), 0)
        self.assertEqual(len(WS_TO_KEY), 0)


def _make_ws_mock(messages):
    """Create a mock websocket that yields the given messages via async for."""
    ws = AsyncMock()
    ws.send = AsyncMock()

    async def async_iter():
        for msg in messages:
            yield msg

    ws.__aiter__ = lambda self: async_iter()
    return ws


class TestRegisterHandler(unittest.TestCase):
    """Test the register async handler."""

    def setUp(self):
        CONNECTIONS.clear()
        WS_TO_KEY.clear()

    def tearDown(self):
        CONNECTIONS.clear()
        WS_TO_KEY.clear()

    def test_register_sends_greeting_and_cleans_up(self):
        """Test that register sends greeting and cleans up on disconnect."""
        from web.server import register

        ws = _make_ws_mock([])

        asyncio.run(register(ws))

        # Should have sent greeting
        ws.send.assert_called_once_with('..:: Hello from the Notification Center ::..')
        # Should have cleaned up
        self.assertEqual(len(CONNECTIONS), 0)
        self.assertEqual(len(WS_TO_KEY), 0)

    def test_register_handles_connected_message(self):
        """Test UUID assignment via 'connected' message."""
        from web.server import register

        connected_msg = json.dumps({'recipient_uuid': 'real-uuid', 'message': 'connected'})
        ws = _make_ws_mock([connected_msg])

        asyncio.run(register(ws))

        # After disconnect, everything should be cleaned up
        self.assertEqual(len(CONNECTIONS), 0)
        self.assertEqual(len(WS_TO_KEY), 0)

    def test_register_forwards_message_to_recipient(self):
        """Test that messages are forwarded to the correct recipient."""
        from web.server import register

        # Set up a recipient
        recipient_ws = AsyncMock()
        recipient_ws.send = AsyncMock()
        _add_connection('target-uuid', recipient_ws)

        # Create sender
        forward_msg = json.dumps({'recipient_uuid': 'target-uuid', 'message': 'hello target'})
        sender_ws = _make_ws_mock([forward_msg])

        asyncio.run(register(sender_ws))

        # Recipient should have received the forwarded message
        recipient_ws.send.assert_called_once_with('hello target')

    def test_register_handles_json_decode_error(self):
        """Test that invalid JSON is handled gracefully."""
        from web.server import register

        ws = _make_ws_mock(['{invalid'])

        # Should not raise
        asyncio.run(register(ws))
        self.assertEqual(len(CONNECTIONS), 0)

    def test_register_warns_on_missing_recipient(self):
        """Test warning when recipient is not found."""
        from web.server import register

        msg = json.dumps({'recipient_uuid': 'nonexistent', 'message': 'hello'})
        ws = _make_ws_mock([msg])

        with patch('web.server.logger') as mock_logger:
            asyncio.run(register(ws))
            # Check that a warning was logged
            mock_logger.warning.assert_called()


class TestPingTimeout(unittest.TestCase):
    """Test that ping_timeout is correctly configured."""

    def test_ping_timeout_less_than_interval(self):
        """Verify ping_timeout < ping_interval in the source code."""
        import re

        with open(os.path.join(os.path.dirname(__file__), '..', 'web', 'server.py'), 'r') as f:
            content = f.read()

        interval_match = re.search(r'ping_interval\s*=\s*(\d+)', content)
        timeout_match = re.search(r'ping_timeout\s*=\s*(\d+)', content)

        self.assertIsNotNone(interval_match, "ping_interval should be set")
        self.assertIsNotNone(timeout_match, "ping_timeout should be set")

        interval = int(interval_match.group(1))
        timeout = int(timeout_match.group(1))

        self.assertLess(timeout, interval,
                        f"ping_timeout ({timeout}) should be less than ping_interval ({interval})")


if __name__ == '__main__':
    unittest.main()
