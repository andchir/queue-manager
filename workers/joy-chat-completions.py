import os
import subprocess
import sys
import time
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from utils.upload_to_gdrive import upload_and_share_file
from utils.upload_file import upload_from_url
from utils.queue_manager import get_queue_next, send_queue_error, send_queue_result

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def processing(queue_item):
    if not queue_item or 'data' not in queue_item:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item

    print(queue_item['data'])

    print('---------------------')
    return queue_item


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('73a7044c-c24b-4fad-9a44-91e04d27f5b3')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
