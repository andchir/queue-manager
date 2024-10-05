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
from utils.upload_file import upload_from_url, delete_old_files
from utils.upload_to_vk import upload_to_vk
from utils.image_resize import image_resize

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


def generate_video(image_file_path, driven_video_name=None):
    if driven_video_name.lower() in ['dance monkey']:
        driving_video_path = '/home/andrew/python_projects/LivePortrait/assets/examples/driving/d6.mp4'
    elif driven_video_name.lower() in ['третье сентября', 'september 3rd']:
        driving_video_path = '/home/andrew/python_projects/LivePortrait/assets/examples/driving/shufutinsky.mp4'
    elif driven_video_name.lower() in ['веселье', 'поцелуи', 'kissing']:
        driving_video_path = '/home/andrew/python_projects/LivePortrait/assets/examples/driving/kisses.pkl'
    elif driven_video_name.lower() in ['masha is fine - уиллем дефо', 'masha is fine - willem dafoe']:
        driving_video_path = '/home/andrew/python_projects/LivePortrait/assets/examples/driving/willem-dafoe-masha-is-fine-25.mp4'
    elif driven_video_name.lower() in ['испанец-хохотун', 'laughing spaniard']:
        driving_video_path = '/home/andrew/python_projects/LivePortrait/assets/examples/driving/ispanets.mp4'
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
    upload_dir_path = os.path.join(ROOT_DIR, 'uploads', 'live-portrait')
    if not queue_item or 'data' not in queue_item:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item
    image_file_path = None
    driven_video_name = queue_item['data']['input'] if 'input' in queue_item['data'] and queue_item['data']['input'] else 'default'

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
    if 'pending' in queue_item:
        print('Pending:', queue_item['pending'])

    print('UUID: ', queue_item['uuid'])
    print('Generating a video...', driven_video_name)

    try:
        image_file_path = image_resize(image_file_path, base_width=800, up_scale=True)
    except Exception as e:
        print('ERROR:', str(e))
        print('Send error message - Unable to determine file type.')
        send_queue_error(queue_item['uuid'], 'Unable to determine file type.')
        return None

    result = generate_video(image_file_path, driven_video_name)
    file_path = result['video'] if result and 'video' in result else None
    if file_path and os.path.isfile(file_path):
        # print('Uploading a file to Google Drive...')
        # shared_file_link = upload_and_share_file(file_path, settings.gdrive_folder_id, type='video')
        print('Uploading a file to YaDisk...')
        try:
            file_url, public_url = upload_and_share_file(file_path, 'api2app/media')
            print('Done.', public_url)
            result_data = {'result': file_url, 'public_url': public_url}
        except Exception as e:
            print('ERROR:', str(e))
            result_data = {}

        if 'upload_url' in queue_item['data'] and queue_item['data']['upload_url'].find('https://pu.vk.com/') == 0:
            print()
            print('Uploading to VK...')
            try:
                vk_resp_data = upload_to_vk(file_path, queue_item['data']['upload_url'])
                if vk_resp_data and 'file' in vk_resp_data:
                    result_data['vk_file_to_save'] = vk_resp_data['file']
                    print('Done.')
            except Exception as e:
                print('ERROR:', str(e))

        print('Sending the result...')
        res = send_queue_result_dict(queue_item['uuid'], result_data)
        print()
        print('Completed.')

        deleted_input = delete_old_files(upload_dir_path, max_hours=2)
        deleted = delete_old_files(os.path.join(upload_dir_path, 'output'), max_hours=2)
        print('Deleted old files: ', deleted + deleted_input)

    else:
        print(f'Output file not found. Send error message - Processing error.')
        send_queue_error(queue_item['uuid'], 'Processing error. Please try again later.')
    print(str(datetime.datetime.now()))
    print('---------------------')
    print('Wait 2 seconds...')
    time.sleep(2)


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('fe10d225-fbae-47b8-9e13-9beb9c1890b8')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
