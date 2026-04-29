"""
Tests for utils/proxy_media_urls.py

Covers URL detection, recursive traversal, embedded-JSON handling,
and the download/replace pipeline (with mocked HTTP requests and filesystem).
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.proxy_media_urls import (
    _is_media_url,
    _process_value,
    proxy_media_in_result,
)

BASE_URL = 'https://queue.example.com'
UPLOAD_DIR = '/tmp/test_proxy_uploads'


def _make_mock_response(content=b'fake-image-data', content_type='image/png', status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = content
    resp.headers = {'Content-Type': content_type}
    resp.raise_for_status = MagicMock()
    return resp


class TestIsMediaUrl(unittest.TestCase):

    def test_recognises_common_image_extensions(self):
        for ext in ('png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'):
            with self.subTest(ext=ext):
                self.assertTrue(_is_media_url(f'https://cdn.example.com/file.{ext}'))

    def test_recognises_video_and_audio_extensions(self):
        for ext in ('mp4', 'mov', 'avi', 'webm', 'mp3', 'wav', 'ogg', 'flac', 'm4a'):
            with self.subTest(ext=ext):
                self.assertTrue(_is_media_url(f'http://cdn.example.com/file.{ext}'))

    def test_rejects_non_media_url(self):
        self.assertFalse(_is_media_url('https://example.com/data.json'))
        self.assertFalse(_is_media_url('https://example.com/page'))
        self.assertFalse(_is_media_url('https://example.com/'))

    def test_rejects_non_url_strings(self):
        self.assertFalse(_is_media_url('just a string'))
        self.assertFalse(_is_media_url(''))
        self.assertFalse(_is_media_url(None))

    def test_url_with_query_string_still_matched(self):
        self.assertTrue(_is_media_url('https://cdn.example.com/photo.jpg?v=123&size=large'))

    def test_rejects_non_http_scheme(self):
        self.assertFalse(_is_media_url('ftp://cdn.example.com/photo.jpg'))
        self.assertFalse(_is_media_url('file:///home/user/photo.jpg'))


class TestProcessValueNoDownload(unittest.TestCase):
    """Tests that do not actually download anything — URLs stay as-is because
    the download is mocked to fail (return None)."""

    def _process(self, value):
        with patch('utils.proxy_media_urls._download_url', return_value=None):
            return _process_value(value, UPLOAD_DIR, BASE_URL)

    def test_plain_non_url_string_unchanged(self):
        self.assertEqual(self._process('hello world'), 'hello world')

    def test_integer_unchanged(self):
        self.assertEqual(self._process(42), 42)

    def test_none_unchanged(self):
        self.assertIsNone(self._process(None))

    def test_dict_keys_preserved(self):
        data = {'state': 'success', 'taskId': 'abc123'}
        result = self._process(data)
        self.assertEqual(result['state'], 'success')
        self.assertEqual(result['taskId'], 'abc123')

    def test_list_elements_processed(self):
        data = ['https://cdn.example.com/a.mp3', 'not-a-url']
        result = self._process(data)
        self.assertEqual(result[1], 'not-a-url')

    def test_embedded_json_string_parsed_and_re_serialised(self):
        inner = {'resultUrls': ['https://cdn.example.com/out.png']}
        value = json.dumps(inner)
        result = self._process(value)
        # Should still be a valid JSON string
        parsed = json.loads(result)
        self.assertIn('resultUrls', parsed)

    def test_deeply_nested_dict(self):
        data = {'a': {'b': {'c': 'not a url'}}}
        result = self._process(data)
        self.assertEqual(result['a']['b']['c'], 'not a url')


class TestProcessValueWithDownload(unittest.TestCase):
    """Tests that verify URLs are replaced when download succeeds."""

    def _process_with_download(self, value, fake_filename='abc.png'):
        with patch('utils.proxy_media_urls._download_url', return_value=fake_filename):
            return _process_value(value, UPLOAD_DIR, BASE_URL)

    def test_bare_media_url_replaced(self):
        url = 'https://tempfile.example.com/image.png'
        result = self._process_with_download(url, 'abc.png')
        self.assertEqual(result, f'{BASE_URL}/uploads/abc.png')

    def test_url_inside_list_replaced(self):
        data = ['https://cdn.example.com/out.png']
        result = self._process_with_download(data, 'xyz.png')
        self.assertEqual(result[0], f'{BASE_URL}/uploads/xyz.png')

    def test_url_inside_dict_value_replaced(self):
        data = {'imageUrl': 'https://cdn.example.com/photo.jpg'}
        result = self._process_with_download(data, 'file.jpg')
        self.assertEqual(result['imageUrl'], f'{BASE_URL}/uploads/file.jpg')

    def test_url_inside_embedded_json_string_replaced(self):
        """resultJson field: a JSON-encoded string containing a URL."""
        inner = {'resultUrls': ['https://tempfile.example.com/result.png']}
        data = {'resultJson': json.dumps(inner)}
        result = self._process_with_download(data, 'proxied.png')
        parsed = json.loads(result['resultJson'])
        self.assertEqual(parsed['resultUrls'][0], f'{BASE_URL}/uploads/proxied.png')

    def test_url_inside_doubly_nested_json_string(self):
        """param field: JSON string whose 'input' value is itself a JSON string."""
        innermost = {'input_urls': ['https://cdn.example.com/input.jpg']}
        inner = {'input': json.dumps(innermost)}
        data = {'param': json.dumps(inner)}
        result = self._process_with_download(data, 'p.jpg')
        outer_parsed = json.loads(result['param'])
        inner_parsed = json.loads(outer_parsed['input'])
        self.assertEqual(inner_parsed['input_urls'][0], f'{BASE_URL}/uploads/p.jpg')


class TestProxyMediaInResult(unittest.TestCase):
    """Integration-level tests for proxy_media_in_result using the real example from the task."""

    SAMPLE_RESULT = {
        'model': 'gpt-image-2-image-to-image',
        'param': (
            '{"input":"{\\"aspect_ratio\\":\\"4:3\\",'
            '\\"prompt\\":\\"Restore this photo\\",'
            '\\"input_urls\\":[\\"https://api2app.s3.cloud.ru/api2app/image/010.jpg\\"]}",'
            '"callBackUrl":"https://queue.api2app.org/queue_result/f6554e00",'
            '"model":"gpt-image-2-image-to-image"}'
        ),
        'state': 'success',
        'taskId': 'a1f059a5b9f3286632a1d15f08789b41',
        'resultJson': '{"resultUrls":["https://tempfile.aiquickdraw.com/images/chatgpt/result.png"]}',
    }

    @patch('utils.proxy_media_urls._download_url')
    def test_result_url_proxied(self, mock_download):
        mock_download.return_value = 'proxied_result.png'
        result = proxy_media_in_result(self.SAMPLE_RESULT, UPLOAD_DIR, BASE_URL)

        result_json = json.loads(result['resultJson'])
        self.assertEqual(
            result_json['resultUrls'][0],
            f'{BASE_URL}/uploads/proxied_result.png',
        )

    @patch('utils.proxy_media_urls._download_url')
    def test_non_media_fields_unchanged(self, mock_download):
        mock_download.return_value = 'f.png'
        result = proxy_media_in_result(self.SAMPLE_RESULT, UPLOAD_DIR, BASE_URL)
        self.assertEqual(result['state'], 'success')
        self.assertEqual(result['taskId'], 'a1f059a5b9f3286632a1d15f08789b41')

    @patch('utils.proxy_media_urls._download_url')
    def test_download_failure_leaves_original_url(self, mock_download):
        mock_download.return_value = None  # simulate failure
        result = proxy_media_in_result(self.SAMPLE_RESULT, UPLOAD_DIR, BASE_URL)
        result_json = json.loads(result['resultJson'])
        # URL should remain untouched
        self.assertIn('tempfile.aiquickdraw.com', result_json['resultUrls'][0])

    @patch('utils.proxy_media_urls._download_url')
    def test_download_called_for_each_media_url(self, mock_download):
        mock_download.return_value = 'x.png'
        data = {
            'urls': ['https://a.com/1.png', 'https://b.com/2.jpg', 'https://c.com/3.gif']
        }
        proxy_media_in_result(data, UPLOAD_DIR, BASE_URL)
        self.assertEqual(mock_download.call_count, 3)


class TestDownloadUrl(unittest.TestCase):
    """Unit tests for the _download_url helper (real filesystem writes, mocked HTTP)."""

    def setUp(self):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    @patch('utils.proxy_media_urls.requests.get')
    def test_file_written_to_disk(self, mock_get):
        mock_get.return_value = _make_mock_response(b'\x89PNG...', 'image/png')
        from utils.proxy_media_urls import _download_url
        filename = _download_url('https://cdn.example.com/photo.png', UPLOAD_DIR)
        self.assertIsNotNone(filename)
        self.assertTrue(filename.endswith('.png'))
        file_path = os.path.join(UPLOAD_DIR, filename)
        self.assertTrue(os.path.isfile(file_path))
        os.remove(file_path)

    @patch('utils.proxy_media_urls.requests.get')
    def test_extension_from_content_type(self, mock_get):
        mock_get.return_value = _make_mock_response(b'data', 'image/webp')
        from utils.proxy_media_urls import _download_url
        filename = _download_url('https://cdn.example.com/photo.unknown', UPLOAD_DIR)
        self.assertTrue(filename.endswith('.webp'))
        os.remove(os.path.join(UPLOAD_DIR, filename))

    @patch('utils.proxy_media_urls.requests.get')
    def test_returns_none_on_http_error(self, mock_get):
        mock_get.side_effect = Exception('Connection refused')
        from utils.proxy_media_urls import _download_url
        result = _download_url('https://cdn.example.com/bad.png', UPLOAD_DIR)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
