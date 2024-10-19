import os
import sys
import time
import random
import requests
import subprocess
import datetime
from gradio_client import Client, file

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.upload_to_yadisk import upload_and_share_file
from config import settings
from utils.queue_manager import send_queue_error, get_queue_next, send_queue_result_dict
from utils.upload_file import upload_from_url, delete_old_files, cut_audio_duration
from utils.upload_to_vk import upload_to_vk
from utils.image_resize import image_resize

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_AUDIO_LENGTH = 60

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


def generate_video_from_photo(image_file_path):
    driving_video_path = '/home/andrew/python_projects/LivePortrait/assets/examples/driving/face_speaking.pkl'

    result = subprocess.run([os.path.join(ROOT_DIR, 'workers', 'live-portrait.sh'), image_file_path,
                             driving_video_path], capture_output=True, text=True)

    output_dir_path = os.path.dirname(image_file_path)
    output_file_name = os.path.join(output_dir_path, 'output', f'{basename(image_file_path)}--{basename(driving_video_path)}.mp4')

    return output_file_name


def processing(queue_item):
    upload_dir_path = os.path.join(ROOT_DIR, 'uploads', 'lip-sync')
    if not queue_item or 'data' not in queue_item:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item
    image_file_path = None
    audio_file_path = None

    if 'audio_file' in queue_item['data']:
        audio_url = queue_item['data']['audio_file']
        try:
            audio_file_path = upload_from_url(upload_dir_path, audio_url, type='audio')
            audio_file_path = cut_audio_duration(audio_file_path, MAX_AUDIO_LENGTH)
        except Exception as e:
            print(f'Error', str(e))

    if 'image_file' in queue_item['data']:
        image_url = queue_item['data']['image_file']
        try:
            image_file_path = upload_from_url(upload_dir_path, image_url)
        except Exception as e:
            print(f'Error', str(e))

    if (not image_file_path or not os.path.isfile(image_file_path)
            or not audio_file_path or not os.path.isfile(audio_file_path)):
        print('Send error message - File not found.')
        send_queue_error(queue_item['uuid'], 'File not found.')
        return None

    print('---------------------')
    if 'pending' in queue_item:
        print('Pending:', queue_item['pending'])

    print('UUID: ', queue_item['uuid'])
    print('Resize image...')

    try:
        image_file_path = image_resize(image_file_path, base_width=800, up_scale=True)
    except Exception as e:
        print('ERROR:', str(e))
        print('Send error message - Unable to determine file type.')
        send_queue_error(queue_item['uuid'], 'Unable to determine file type.')
        return None

    print('Step 1: Generating a video from photo...')
    out_video_file_path = generate_video_from_photo(image_file_path)
    if not out_video_file_path or not os.path.isfile(out_video_file_path):
        print(f'Output file not found. Send error message - Processing error.')
        send_queue_error(queue_item['uuid'], 'Processing error. Please try again later.')

    print('Step 1 - Done.')

    if out_video_file_path and os.path.isfile(out_video_file_path):
        # print('Uploading a file to Google Drive...')
        # shared_file_link = upload_and_share_file(file_path, settings.gdrive_folder_id, type='video')
        print('Uploading a file to YaDisk...')
        try:
            file_url, public_url = upload_and_share_file(out_video_file_path, 'api2app/media')
            print('Done.', public_url)
            result_data = {'result': file_url, 'public_url': public_url}
        except Exception as e:
            print('ERROR:', str(e))
            result_data = {}

        print('Sending the result...')
        res = send_queue_result_dict(queue_item['uuid'], result_data)
        print()
        print('Completed.')

        deleted_input = delete_old_files(upload_dir_path, max_hours=2)
        deleted = delete_old_files(os.path.join(upload_dir_path, 'output'), max_hours=2)
        print('Deleted old files: ', deleted + deleted_input)

    print(str(datetime.datetime.now()))
    print('---------------------')
    print('Wait 2 seconds...')
    time.sleep(2)


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('068a33f4-9b1f-4fe2-8263-85395edf32cf')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
