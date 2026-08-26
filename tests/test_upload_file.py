import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException, status

from config import Settings
from utils.upload_file import validate_file_size


class ValidateFileSizeTestCase(unittest.TestCase):
    def test_default_limits_are_used_when_env_values_are_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            default_settings = Settings(_env_file=None)

        self.assertEqual(default_settings.image_max_file_size, 20 * 1024 * 1024)
        self.assertEqual(default_settings.audio_max_file_size, 20 * 1024 * 1024)
        self.assertEqual(default_settings.video_max_file_size, 100 * 1024 * 1024)

    @patch('utils.upload_file.settings')
    def test_uses_configured_limit_for_each_file_type(self, mock_settings):
        mock_settings.image_max_file_size = 10
        mock_settings.audio_max_file_size = 20
        mock_settings.video_max_file_size = 30

        self.assertTrue(validate_file_size(10, type='image'))
        self.assertTrue(validate_file_size(20, type='audio'))
        self.assertTrue(validate_file_size(30, type='video'))

        for file_type, file_size in [('image', 11), ('audio', 21), ('video', 31)]:
            with self.subTest(file_type=file_type):
                with self.assertRaises(HTTPException) as error:
                    validate_file_size(file_size, type=file_type)
                self.assertEqual(error.exception.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
                self.assertEqual(
                    error.exception.detail,
                    f'The file is too large. Maximum file size is {file_size - 1} bytes.',
                )
