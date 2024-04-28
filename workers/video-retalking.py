import os
import sys
import time
import requests
import base64
import uuid
from gradio_client import Client, file

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.upload_to_gdrive import upload_and_share_file
from config import settings

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# https://github.com/OpenTalker/video-retalking
# Start API:
# python webUI.py
# Start worker:
# python workers/video-retalking.py


def get_queue_next(task_uuid):
    queue_url = 'https://queue.api2app.ru/queue_next/{}'.format(task_uuid)
    r = requests.get(url=queue_url)
    return r.json() if r.status_code == 200 else None


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
        'steps': 40,
        'width': 768,
        'height': 768,
        'cfg_scale': 5,
        'sampler_name': 'DPM++ 3M SDE',
        'scheduler': 'Exponential',
        'sd_model_name': 'newrealityxlAllInOne_30Experimental',
        'sd_model_hash': '69cc62d2b6',
        'restore_faces': True,
        'save_images': False,
        'send_images': True
    }

    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = response.json()

    output_dir_path = os.path.join(ROOT_DIR, 'output')
    if not os.path.exists(output_dir_path):
        os.mkdir(output_dir_path)

    file_name = str(uuid.uuid1()) + '.png'

    with open(os.path.join(output_dir_path, file_name), 'wb') as f:
        f.write(base64.b64decode(r['images'][0]))

    return os.path.join(output_dir_path, file_name)


def processing(queue_item):
    client = Client('http://127.0.0.1:7860/')
    if queue_item:
        print('---------------------')
        print('Generating a video...')
        print(queue_item['data'])
        result = client.predict(
            segment_length=15,
            video={"video": file('/media/andrew/KINGSTON/video/green_screen/Masseuse.mp4')},
            audio=file('/media/andrew/KINGSTON/work/SadTalker/input_audio/W_4_DEV_1.mp3'),
            api_name="/convert"
        )
        print(result)
        print('Completed.')
        print('---------------------')
    else:
        print('Waiting for a task...')
    # if queue_item and 'uuid' in queue_item and 'data' in queue_item and 'prompt' in queue_item['data']:
    #     prompt = queue_item['data']['prompt'] if 'prompt' in queue_item['data'] else ''
    #     negative_prompt = queue_item['data']['negative_prompt'] if 'negative_prompt' in queue_item['data'] else ''
    #     print('---------------------')
    #     print('Prompt: {}'.format(prompt))
    #     print('Generating an image...')
    #     file_path = generate_image(prompt, negative_prompt)
    #     print('Done.')
    #     if file_path and os.path.isfile(file_path):
    #         print('Uploading a file to Google Drive...')
    #         shared_file_link = upload_and_share_file(file_path, settings.gdrive_folder_id)
    #         print('Done.')
    #         print('Sending the result...')
    #         res = send_queue_result(queue_item['uuid'], shared_file_link)
    #         print('Completed.')
    #         print('---------------------')
    #     else:
    #         print(f'{file_path} not found.')
    # else:
    #     print('Waiting for a task...')
    return queue_item


if __name__ == '__main__':
    while True:
        queue_item = get_queue_next('d9600585-1449-42be-a742-5fd5e62688d6')
        if queue_item is not None:
            processing(queue_item)
        else:
            print('Waiting for a task...')
            time.sleep(10)
