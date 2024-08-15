import os
import sys
import time
import random
import requests
import subprocess
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


def prefix(filename):
    """a.jpg -> a"""
    pos = filename.rfind(".")
    if pos == -1:
        return filename
    return filename[:pos]


def basename(filename):
    """a/b/c.jpg -> c"""
    return prefix(os.path.basename(filename))


def generate_video(image_file_path, driven_video_name):
    if driven_video_name.lower() in ['dance monkey']:
        driving_video_path = '/home/andrew/python_projects/LivePortrait/assets/examples/driving/d6.mp4'
    elif driven_video_name.lower() in ['третье сентября']:
        driving_video_path = '/home/andrew/python_projects/LivePortrait/assets/examples/driving/shufutinsky.mp4'
    else:
        driving_video_path = random.choice([
            '/home/andrew/python_projects/LivePortrait/assets/examples/driving/marta1.pkl',
            '/home/andrew/python_projects/LivePortrait/assets/examples/driving/marta2.pkl',
            '/home/andrew/python_projects/LivePortrait/assets/examples/driving/marta3.pkl',
        ])

    if driving_video_path is None:
        return None

    # print(driving_video_path)

    result = subprocess.run([os.path.join(ROOT_DIR, 'workers', 'live-portrait.sh'), image_file_path,
                             driving_video_path], capture_output=True, text=True)

    print(result.stderr, result.stdout)

    output_dir_path = os.path.dirname(image_file_path)
    output_file_name = os.path.join(output_dir_path, 'output', f'{basename(image_file_path)}--{basename(driving_video_path)}.mp4')

    print(output_file_name)

    return {'video': output_file_name}


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
    print('Generating a video...', driven_video_name)
    result = generate_video(image_file_path, driven_video_name)
    file_path = result['video'] if result and 'video' in result else None
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
