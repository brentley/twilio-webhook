import json
import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from webhook import app, save_to_s3, save_json_and_content  # Import your Flask app and functions

BUCKET_NAME = os.environ.get("DB_NAME")

class TestWebhook(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('webhook.s3.put_object')
    def test_save_to_s3(self, mock_put_object):
        data = {"key": "value"}
        filename = "test_file.json"
        save_to_s3(data, filename)
        json_data = json.dumps(data)
        mock_put_object.assert_called_with(Bucket=BUCKET_NAME, Key=filename, Body=json_data)

    @patch('webhook.save_to_s3')
    def test_save_json_and_content(self, mock_save_to_s3):
        json_data = {"content": "example", "other_key": "value", "sender": "test_sender"}
        prefix = "test_prefix"
        timestamp_regex = r'\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}'
        save_json_and_content(json_data, prefix)
        mock_save_to_s3.assert_any_call(json_data, unittest.mock.ANY)
        mock_save_to_s3.assert_any_call("example", unittest.mock.ANY)
        mock_save_to_s3.assert_any_call("example", "test_sender_content.txt")
        self.assertRegex(mock_save_to_s3.call_args_list[0][0][1], f"{prefix}_{timestamp_regex}.json")
        self.assertRegex(mock_save_to_s3.call_args_list[1][0][1], f"{prefix}_content_{timestamp_regex}.txt")

    @patch('webhook.save_json_and_content')
    def test_receive_data(self, mock_save_json_and_content):
        response = self.app.post('/', json={"key": "value"})
        mock_save_json_and_content.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "JSON data and content saved"})

    @patch('webhook.s3.list_objects_v2')
    @patch('webhook.s3.get_object')
    def test_display_last_message(self, mock_get_object, mock_list_objects_v2):
        # Simulate S3 returning a list of objects
        mock_list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'json_data_content_2023-01-01-12-00-00.txt', 'LastModified': datetime(2023, 1, 1, 12, 0, 0)},
                {'Key': 'json_data_2023-01-01-12-00-00.json', 'LastModified': datetime(2023, 1, 1, 12, 0, 0)}
            ]
        }

        # Simulate the content of the latest content file
        mock_get_object.return_value = {
            'Body': MagicMock(read=lambda: b'Your One-Time Passcode is 650355.')
        }

        # Make the GET request
        response = self.app.get('/')

        # Check the status code and content of the response
        self.assertEqual(response.status_code, 200)
        self.assertIn('Most Recent Message', response.data.decode())
        self.assertIn('Your One-Time Passcode is 650355.', response.data.decode())

if __name__ == '__main__':
    unittest.main()

