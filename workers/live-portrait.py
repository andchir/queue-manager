import os
import sys
import time
import requests
from gradio_client import Client, file

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from utils.queue_manager import send_queue_error, get_queue_next, send_queue_result
from utils.upload_file import upload_from_url
from utils.upload_to_gdrive import upload_and_share_file

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# https://github.com/KwaiVGI/LivePortrait
# Start API:
# python app.py
# python app_animals.py
# Start worker:
# python workers/live-portrait.py


def generate_video(image_file_path, driven_video_name):

    print(image_file_path, driven_video_name)

    # client = Client('http://127.0.0.1:7860/')
    # result = client.predict(
    #     source_image=file(image_file_path),
    #     preprocess='full',
    #     still_mode=True,
    #     use_enhancer=True,
    #     batch_size=2,
    #     size=256,
    #     pose_style=0,
    #     api_name='/test_1'
    # )
    # return result

    return {}


def processing(queue_item):
    upload_dir_path = os.path.join(ROOT_DIR, 'uploads')
    if not queue_item or 'data' not in queue_item:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item
    image_file_path = None
    driven_video_name = queue_item['data']['input'] if 'input' in queue_item['data'] else 'default'

    if 'image_file' in queue_item['data']:
        image_url = queue_item['data']['image_file']
        try:
            image_file_path = upload_from_url(upload_dir_path, image_url)
        except Exception as e:
            print(f'Error', str(e))
            send_queue_error(queue_item['uuid'], str(e))
            return None

    if not image_file_path or not os.path.isfile(image_file_path):
        print('Send error message - Please upload image file.')
        send_queue_error(queue_item['uuid'], 'Please upload image file.')
        return None

    print('---------------------')
    print('Generating a video...')
    result = generate_video(image_file_path, driven_video_name)
    file_path = result['video'] if 'video' in result else None
    if file_path and os.path.isfile(file_path):
        print('Uploading a file to Google Drive...')
        shared_file_link = upload_and_share_file(file_path, settings.gdrive_folder_id, type='video')
        print('Done.')
        print('Sending the result...')
        res = send_queue_result(queue_item['uuid'], shared_file_link)
        print('Completed.')
    else:
        print(f'Output file not found. Send error message - Processing error.')
        send_queue_error(queue_item['uuid'], 'Processing error. Please try again later.')
    print('---------------------')


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('304a0d98-216b-45d2-bf63-56811e49ab6b')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
