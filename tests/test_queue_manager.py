"""
Tests for utils/queue_manager.py
Specifically testing network change scenarios and timeout handling.
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
import requests
from requests.exceptions import Timeout, ConnectionError, RequestException
import time
import threading

# Import functions to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.queue_manager import (
    get_queue_next,
    send_queue_result,
    send_queue_result_dict,
    send_queue_error,
    polling_queue
)


class TestQueueManagerNetworkChanges(unittest.TestCase):
    """Test queue manager functions handle network changes gracefully"""

    def setUp(self):
        """Set up test fixtures"""
        self.task_uuid = 'test-task-uuid-123'
        self.queue_uuid = 'test-queue-uuid-456'

    @patch('utils.queue_manager.settings')
    @patch('utils.queue_manager.requests.get')
    def test_get_queue_next_timeout(self, mock_get, mock_settings):
        """Test that get_queue_next handles timeout without hanging"""
        mock_settings.app_server_name = 'example.com'
        mock_get.side_effect = Timeout("Connection timed out")

        result = get_queue_next(self.task_uuid)

        self.assertIsNone(result)
        mock_get.assert_called_once_with(
            url=f'https://example.com/queue_next/{self.task_uuid}',
            timeout=30
        )

    @patch('utils.queue_manager.settings')
    @patch('utils.queue_manager.requests.get')
    def test_get_queue_next_connection_error(self, mock_get, mock_settings):
        """Test that get_queue_next handles connection errors (e.g., VPN disconnect)"""
        mock_settings.app_server_name = 'example.com'
        mock_get.side_effect = ConnectionError("Network is unreachable")

        result = get_queue_next(self.task_uuid)

        self.assertIsNone(result)

    @patch('utils.queue_manager.settings')
    @patch('utils.queue_manager.requests.get')
    def test_get_queue_next_with_custom_timeout(self, mock_get, mock_settings):
        """Test that get_queue_next respects custom timeout parameter"""
        mock_settings.app_server_name = 'example.com'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'test': 'value'}}
        mock_get.return_value = mock_response

        custom_timeout = 10
        result = get_queue_next(self.task_uuid, timeout=custom_timeout)

        mock_get.assert_called_once_with(
            url=f'https://example.com/queue_next/{self.task_uuid}',
            timeout=custom_timeout
        )
        self.assertIsNotNone(result)

    @patch('utils.queue_manager.settings')
    @patch('utils.queue_manager.requests.post')
    def test_send_queue_result_timeout(self, mock_post, mock_settings):
        """Test that send_queue_result handles timeout"""
        mock_settings.app_server_name = 'example.com'
        mock_post.side_effect = Timeout("Connection timed out")

        result = send_queue_result(self.queue_uuid, "test result")

        self.assertIsNone(result)

    @patch('utils.queue_manager.settings')
    @patch('utils.queue_manager.requests.post')
    def test_send_queue_result_dict_timeout(self, mock_post, mock_settings):
        """Test that send_queue_result_dict handles timeout"""
        mock_settings.app_server_name = 'example.com'
        mock_post.side_effect = Timeout("Connection timed out")

        result = send_queue_result_dict(self.queue_uuid, {'key': 'value'})

        self.assertIsNone(result)

    @patch('utils.queue_manager.settings')
    @patch('utils.queue_manager.requests.post')
    def test_send_queue_error_timeout(self, mock_post, mock_settings):
        """Test that send_queue_error handles timeout"""
        mock_settings.app_server_name = 'example.com'
        mock_post.side_effect = Timeout("Connection timed out")

        result = send_queue_error(self.queue_uuid, "error message")

        self.assertIsNone(result)

    @patch('utils.queue_manager.get_queue_next')
    def test_polling_queue_continues_after_network_error(self, mock_get_queue_next):
        """
        Test that polling_queue continues running even when network fails.
        This is the main test for the issue - simulating VPN disconnect/reconnect.
        """
        # Simulate network failure then recovery
        call_count = [0]
        max_calls = 3

        def side_effect_network_change(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: network error (e.g., VPN disconnected)
                return None
            elif call_count[0] == 2:
                # Second call: still no connection
                return None
            elif call_count[0] >= max_calls:
                # Third call: network recovered
                return {'data': {'task': 'test'}, 'uuid': 'test-uuid'}
            return None

        mock_get_queue_next.side_effect = side_effect_network_change

        # Track if callback was called
        callback_called = [False]

        def test_callback(queue_item):
            callback_called[0] = True

        # Run polling in a thread with a timeout
        def run_polling():
            polling_queue(self.task_uuid, test_callback, interval_sec=0.1)

        polling_thread = threading.Thread(target=run_polling, daemon=True)
        polling_thread.start()

        # Wait for polling to complete a few iterations
        time.sleep(0.5)

        # Verify callback was eventually called (network recovered)
        self.assertTrue(callback_called[0], "Callback should be called after network recovery")
        self.assertGreaterEqual(call_count[0], max_calls, "Should have made multiple polling attempts")

    @patch('utils.queue_manager.get_queue_next')
    def test_polling_queue_handles_none_gracefully(self, mock_get_queue_next):
        """Test that polling_queue handles None return values gracefully"""
        # Return None for the first few calls
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                return None
            return {'data': {'task': 'test'}, 'uuid': 'test-uuid'}

        mock_get_queue_next.side_effect = side_effect

        callback_called = [False]

        def test_callback(queue_item):
            callback_called[0] = True

        # Run polling in a thread
        def run_polling():
            polling_queue(self.task_uuid, test_callback, interval_sec=0.05)

        polling_thread = threading.Thread(target=run_polling, daemon=True)
        polling_thread.start()

        # Wait for polling iterations
        time.sleep(0.3)

        # Verify it eventually got a result
        self.assertTrue(callback_called[0])
        self.assertGreaterEqual(call_count[0], 2)


class TestQueueManagerTimeoutValues(unittest.TestCase):
    """Test that timeout parameters work correctly"""

    @patch('utils.queue_manager.settings')
    @patch('utils.queue_manager.requests.get')
    def test_get_queue_next_default_timeout(self, mock_get, mock_settings):
        """Test default timeout is 30 seconds"""
        mock_settings.app_server_name = 'example.com'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {}}
        mock_get.return_value = mock_response

        get_queue_next('uuid-123')

        # Verify timeout was passed
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['timeout'], 30)

    @patch('utils.queue_manager.settings')
    @patch('utils.queue_manager.requests.post')
    def test_send_queue_result_custom_timeout(self, mock_post, mock_settings):
        """Test custom timeout parameter for send_queue_result"""
        mock_settings.app_server_name = 'example.com'
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        send_queue_result('uuid-123', 'result', timeout=15)

        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['timeout'], 15)


if __name__ == '__main__':
    unittest.main()
