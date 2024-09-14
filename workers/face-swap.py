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

# https://github.com/andchir/insightface_gfpgan
# Start worker:
# python workers/face-swap.py


def generate(source_image_path, face_image_path):

    result = subprocess.run([os.path.join(ROOT_DIR, 'workers', 'face-swap.sh'), source_image_path,
                             face_image_path], capture_output=True, text=True)

    print(result.stderr, result.stdout)

    basename = os.path.basename(source_image_path)
    output_dir_path = os.path.dirname(source_image_path)
    output_file_name = os.path.join(output_dir_path, 'output', basename)

    print(output_file_name)

    return output_file_name


def processing(queue_item):
    upload_dir_path = os.path.join(ROOT_DIR, 'uploads', 'face-swap')
    if not queue_item or 'data' not in queue_item:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item
    image_file_path = None
    image2_file_path = None

    if 'image_file' in queue_item['data']:
        image_url = queue_item['data']['image_file']
        try:
            image_file_path = upload_from_url(upload_dir_path, image_url)
        except Exception as e:
            print(f'Error', str(e))
            send_queue_error(queue_item['uuid'], str(e))
            return None

    if 'image_file2' in queue_item['data']:
        image_url2 = queue_item['data']['image_file2']
        try:
            image2_file_path = upload_from_url(upload_dir_path, image_url2)
        except Exception as e:
            print(f'Error', str(e))
            send_queue_error(queue_item['uuid'], str(e))
            return None

    if not image_file_path or not os.path.isfile(image_file_path) or not image2_file_path or not os.path.isfile(image2_file_path):
        print('Send error message - Please upload image file.')
        send_queue_error(queue_item['uuid'], 'Please upload image file.')
        return None

    print('---------------------')
    if 'pending' in queue_item:
        print('Pending:', queue_item['pending'])

    print('Processing...')

    try:
        image_file_path = image_resize(image_file_path, base_width=3000)
        image2_file_path = image_resize(image2_file_path, base_width=3000)
    except Exception as e:
        print('ERROR:', str(e))
        print('Send error message - Unable to determine file type.')
        send_queue_error(queue_item['uuid'], 'Unable to determine file type.')
        return None

    file_path = generate(image_file_path, image2_file_path)
    if file_path and os.path.isfile(file_path):
        print('Uploading a file to YaDisk...')
        file_url, public_url = upload_and_share_file(file_path, 'api2app/media')
        print('Done.', public_url)

        result_data = {'result': file_url, 'public_url': public_url}

        # if 'upload_url' in queue_item['data'] and queue_item['data']['upload_url'].find('https://pu.vk.com/') == 0:
        #     print()
        #     print('Uploading to VK...')
        #     try:
        #         vk_resp_data = upload_to_vk(file_path, queue_item['data']['upload_url'])
        #         if vk_resp_data and 'file' in vk_resp_data:
        #             result_data['vk_file_to_save'] = vk_resp_data['file']
        #             print('Done.')
        #     except Exception as e:
        #         print('ERROR:', str(e))

        print('Sending the result...')
        res = send_queue_result_dict(queue_item['uuid'], result_data)
        print()
        print('Completed.')

        deleted_input = delete_old_files(upload_dir_path, max_hours=3)
        print('Deleted old files: ', deleted_input)
    else:
        print(f'Output file not found. Send error message - Processing error.')
        send_queue_error(queue_item['uuid'], 'Processing error. Please try again later.')
    print(str(datetime.datetime.now()))
    print('---------------------')


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('e54e4333-44dc-408f-86fd-8bb66e4da923')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
