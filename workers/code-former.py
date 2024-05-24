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
    upload_dir_path = os.path.join(ROOT_DIR, 'uploads')
    if not queue_item or 'data' not in queue_item:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item
    image_file_path = None

    if 'image_file' in queue_item['data']:
        image_url = queue_item['data']['image_file']
        image_file_path = upload_from_url(upload_dir_path, image_url)

    if not image_file_path or not os.path.isfile(image_file_path):
        print('Send error message - Please upload image file.')
        send_queue_error(queue_item['uuid'], 'Please upload image file.')
        return None

    print('---------------------')
    print('Processing...')

    dir_path = os.path.dirname(image_file_path)
    file_basename = os.path.basename(image_file_path)
    result = subprocess.run([os.path.join(ROOT_DIR, 'workers', 'code-former.sh'), image_file_path],
                            capture_output=True, text=True)

    print(result.stdout)

    file_path = os.path.join(
        dir_path,
        'output',
        'final_results',
        file_basename.replace('.jpg', '.png').replace('.jpeg', '.png')
    )
    if file_path and os.path.isfile(file_path):
        print('Uploading a file to Google Drive...')
        shared_file_link = upload_and_share_file(file_path, settings.gdrive_folder_id, type='image')
        print('Done.')
        print('Sending the result...')
        res = send_queue_result(queue_item['uuid'], shared_file_link)
        print('Completed.')
    else:
        print(f'Output file not found. Send error message - Processing error.')
        send_queue_error(queue_item['uuid'], 'Processing error. Please try again later.')
    print('---------------------')
    return queue_item


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('8c595969-139a-40ec-87f5-f523d02f7f4a')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
