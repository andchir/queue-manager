import os
import sys
import requests
import base64
import uuid

sys.path.append(os.path.abspath('.'))
from utils.upload_to_gdrive import upload_and_share_file
from config import settings

# https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
# Start API:
# python webui.py --api


def get_queue_next(task_uuid):
    queue_url = 'https://queue.api2app.ru/queue_next/{}'.format(task_uuid)
    r = requests.get(url=queue_url)
    return r.json()


def send_queue_result(queue_uuid, result_str):
    queue_url = 'https://queue.api2app.ru/queue_result/{}'.format(queue_uuid)
    payload = {
        'result_data': {'image': result_str}
    }
    r = requests.post(url=queue_url, json=payload)
    return r.json()


def generate_image(prompt, negative_prompt=''):
    url = 'http://127.0.0.1:7860'

    payload = {
        'prompt': prompt,
        'negative_prompt': negative_prompt,
        'steps': 20,
        'width': 768,
        'height': 768,
        'sampler_name': 'LCM',
        'save_images': False,
        'send_images': True
    }

    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = response.json()

    output_dir_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    if not os.path.exists(output_dir_path):
        os.mkdir(output_dir_path)

    file_name = str(uuid.uuid1()) + '.png'

    with open(os.path.join(output_dir_path, file_name), 'wb') as f:
        f.write(base64.b64decode(r['images'][0]))

    return os.path.join(output_dir_path, file_name)


if __name__ == '__main__':
    queue_item = get_queue_next('c3a138bb-9b73-4543-8090-fc4f90e2bae8')
    if queue_item and 'uuid' in queue_item and 'data' in queue_item and 'prompt' in queue_item['data']:
        prompt = queue_item['data']['prompt'] if 'prompt' in queue_item['data'] else ''
        negative_prompt = queue_item['data']['negative_prompt'] if 'negative_prompt' in queue_item['data'] else ''
        file_path = generate_image(prompt, negative_prompt)
        if file_path:
            shared_file_link = upload_and_share_file(file_path, settings.gdrive_folder_id)
            res = send_queue_result(queue_item['uuid'], shared_file_link.replace('&export=download', '&authuser=0'))
            print('Done.')
    else:
        print('Queue is empty.')
