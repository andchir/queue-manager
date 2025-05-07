import json

import requests
import time
from config import settings
from utils.upload_file import upload_from_url


def is_json(json_str: str) -> bool:
    json_str = json_str.strip()
    # if not re.fullmatch(r'^(\[.*\]|\{.*\})$', json_str):
    #     return False
    try:
        json.loads(json_str)
        return True
    except ValueError:
        return False


def get_queue_next(task_uuid):
    queue_url = 'https://{}/queue_next/{}'.format(settings.app_server_name, task_uuid)
    try:
        r = requests.get(url=queue_url)
    except Exception as e:
        print(str(e))
        return None
    result = r.json() if r.status_code == 200 else None
    return result if result and 'data' in result else None


def send_queue_result(queue_uuid, result_str, key='result'):
    queue_url = 'https://{}/queue_result/{}'.format(settings.app_server_name, queue_uuid)
    payload = {
        'result_data': dict(zip([key], [result_str]))
    }
    try:
        r = requests.post(url=queue_url, json=payload)
    except Exception as e:
        print(e)
        return None
    return r.json()


def send_queue_result_dict(queue_uuid, result_dict):
    queue_url = 'https://{}/queue_result/{}'.format(settings.app_server_name, queue_uuid)
    payload = {
        'result_data': result_dict
    }
    try:
        r = requests.post(url=queue_url, json=payload)
    except Exception as e:
        print(e)
        return None
    return r.json()


def send_queue_error(queue_uuid, message):
    queue_url = 'https://{}/queue_error/{}'.format(settings.app_server_name, queue_uuid)
    payload = {'message': message}
    try:
        r = requests.post(url=queue_url, data=payload)
    except Exception as e:
        print(e)
        return None
    return r.json()


def polling_queue(item_uuid, callback_func, interval_sec=10):
    show_message = True
    while True:
        queue_item = get_queue_next(item_uuid)
        if queue_item is not None:
            callback_func(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(interval_sec)


def upload_queue_files(queue_item, upload_dir_path):
    image_file_path = None
    image_file_path2 = None
    audio_file_path = None
    video_file_path = None

    if 'video_file' in queue_item['data']:
        video_url = queue_item['data']['video_file']
        try:
            video_file_path = upload_from_url(upload_dir_path, video_url, type='video')
        except Exception as e:
            print(f'Error', str(e))

    if 'audio_file' in queue_item['data'] or 'audio_url' in queue_item['data']:
        audio_url = queue_item['data']['audio_file']\
            if 'audio_file' in queue_item['data'] else queue_item['data']['audio_url']
        try:
            audio_file_path = upload_from_url(upload_dir_path, audio_url, type='audio')
        except Exception as e:
            print(f'Error', str(e))

    if 'image_file' in queue_item['data']:
        image_url = queue_item['data']['image_file']
        try:
            image_file_path = upload_from_url(upload_dir_path, image_url)
        except Exception as e:
            print(f'Error', str(e))

    if 'image_file2' in queue_item['data']:
        image_url2 = queue_item['data']['image_file2']
        try:
            image_file_path2 = upload_from_url(upload_dir_path, image_url2)
        except Exception as e:
            print(f'Error', str(e))

    return image_file_path, audio_file_path, video_file_path, image_file_path2
