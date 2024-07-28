import os
import subprocess
import sys
import time
from gradio_client import Client, file
from utils.queue_manager import get_queue_next, send_queue_error, send_queue_result
from utils.upload_file import upload_from_url, cut_audio_duration
from utils.upload_to_gdrive import upload_and_share_file
from config import settings

# https://github.com/BadToBest/EchoMimic
# Start API:
# export FFMPEG_PATH=/usr/bin/ffmpeg
# python -u webgui.py --server_port=3000
# Start worker:
# python workers/echo-mimic.py

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_AUDIO_LENGTH = 30


def generate_video(image_file_path, audio_file_path):
    client = Client('http://127.0.0.1:3000/')
    result = client.predict(
        uploaded_img=file(image_file_path),
        uploaded_audio=file(audio_file_path),
        width=512,
        height=512,
        length=1200,
        seed=420,
        facemask_dilation_ratio=0.1,
        facecrop_dilation_ratio=0.5,
        context_frames=12,
        context_overlap=3,
        cfg=2.5,
        steps=30,
        sample_rate=16000,
        fps=24,
        device="cuda",
        api_name="/generate_video"
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
            audio_file_path = cut_audio_duration(audio_file_path, MAX_AUDIO_LENGTH)

        if not image_file_path or not audio_file_path:
            print('Send error message')
            send_queue_error(queue_item['uuid'], 'Please upload image and audio files.')
            return None

        print('---------------------')
        print('Generating a video...')
        # result = generate_video(image_file_path, audio_file_path)
        # file_path = result['video'] if 'video' in result else None
        # if file_path and os.path.isfile(file_path):
        #     print('Uploading a file to Google Drive...')
        #     shared_file_link = upload_and_share_file(file_path, settings.gdrive_folder_id, type='video')
        #     print('Done.')
        #     print('Sending the result...')
        #     res = send_queue_result(queue_item['uuid'], shared_file_link)
        #     print('Completed.')
        # else:
        #     print(f'Output file not found.')
        # print('---------------------')
    else:
        print('Waiting for a task...')
    return queue_item


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('37ecfff5-b716-421f-b3b4-370d89acb3d1')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
