import os
import sys
import time
import requests
import base64
import uuid
from gradio_client import Client, file

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.upload_file import upload_from_url
from utils.upload_to_gdrive import upload_and_share_file
from config import settings

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# https://github.com/vinthony/SadTalker.git
# Start API:
# python app_sadtalker.py
# Start worker:
# python workers/sad-talker.py


def get_queue_next(task_uuid):
    queue_url = 'https://queue.api2app.ru/queue_next/{}'.format(task_uuid)
    r = requests.get(url=queue_url)
    return r.json() if r.status_code == 200 else None


def send_queue_result(queue_uuid, result_str):
    queue_url = 'https://queue.api2app.ru/queue_result/{}'.format(queue_uuid)
    payload = {
        'result_data': {'video': result_str}
    }
    r = requests.post(url=queue_url, json=payload)
    return r.json()


def send_queue_error(queue_uuid, message):
    queue_url = 'https://queue.api2app.ru/queue_error/{}'.format(queue_uuid)
    payload = {'message': message}
    r = requests.post(url=queue_url, data=payload)
    return r.json()


def generate_video(image_file_path, audio_file_path):
    client = Client('http://127.0.0.1:7860/')
    result = client.predict(
        source_image=file(image_file_path),
        driven_audio=file(audio_file_path),
        preprocess='crop',
        still_mode=True,
        use_enhancer=True,
        batch_size=1,
        size=256,
        pose_style=0,
        api_name='/test_1'
    )
    return result


def processing(queue_item):
    upload_dir_path = os.path.join(ROOT_DIR, 'uploads')
    if queue_item and 'data' in queue_item:
        image_file_path = None
        audio_file_path = None

        if 'image_file' in queue_item['data']:
            image_url = queue_item['data']['image_file']
            image_file_path = upload_from_url(upload_dir_path, image_url)

        if 'audio_file' in queue_item['data']:
            audio_url = queue_item['data']['audio_file']
            audio_file_path = upload_from_url(upload_dir_path, audio_url)

        if not image_file_path or not audio_file_path:
            print('Send error message')
            send_queue_error(queue_item['uuid'], 'Please upload image and audio files.')
            return None

        print('---------------------')
        print('Generating a video...')
        result = generate_video(image_file_path, audio_file_path)
        file_path = result['video'] if 'video' in result else None
        if file_path and os.path.isfile(file_path):
            print('Uploading a file to Google Drive...')
            shared_file_link = upload_and_share_file(file_path, settings.gdrive_folder_id, type='video')
            print('Done.')
            print('Sending the result...')
            res = send_queue_result(queue_item['uuid'], shared_file_link)
            print('Completed.')
        else:
            print(f'Output file not found.')
        print('---------------------')
    else:
        print('Waiting for a task...')
    return queue_item


if __name__ == '__main__':
    while True:
        queue_item = get_queue_next('6dfa6f22-5450-471c-97b5-099cdf68c511')
        if queue_item is not None:
            processing(queue_item)
        else:
            print('Waiting for a task...')
            time.sleep(10)
