import os
import subprocess
import sys
import time
import datetime
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.upload_to_yadisk import upload_and_share_file
from utils.upload_file import upload_from_url, delete_old_files
from utils.queue_manager import get_queue_next, send_queue_error, send_queue_result, send_queue_result_dict
from utils.image_resize import image_resize, convert_to_jpg
from utils.upload_to_vk import upload_to_vk

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# https://github.com/zsyOAOA/InvSR
# Start worker:
# python workers/invsr-upscaler.py

def processing(queue_item):
    upload_dir_path = os.path.join(ROOT_DIR, 'uploads', 'invsr-upscaler')
    if not queue_item or 'data' not in queue_item:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item
    image_file_path = None

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
    print('Processing...')

    try:
        image_file_path = image_resize(image_file_path, base_width=800)
    except Exception as e:
        print('ERROR:', str(e))
        print('Send error message - Unable to determine file type.')
        send_queue_error(queue_item['uuid'], 'Unable to determine file type.')
        return None

    dir_path = os.path.dirname(image_file_path)
    file_basename = str(os.path.basename(image_file_path))
    result = subprocess.run([os.path.join(ROOT_DIR, 'workers', 'invsr-upscaler.sh'), image_file_path],
                            capture_output=True, text=True)

    # print(result.stdout)

    file_path = os.path.join(dir_path, 'output',
                             file_basename.replace('.jpg', '.png').replace('.jpeg', '.png'))

    print(file_path)

    if file_path and os.path.isfile(file_path):
        # print('Uploading a file to Google Drive...')
        # shared_file_link = upload_and_share_file(file_path, settings.gdrive_folder_id, type='image')

        print('Converting to JPG...')
        file_path = convert_to_jpg(file_path)

        print('Uploading a file to YaDisk...')
        try:
            file_url, public_url = upload_and_share_file(file_path, 'api2app/media')
            print('Done.', public_url)
            result_data = {'result': file_url, 'public_url': public_url}
        except Exception as e:
            print('ERROR:', str(e))
            result_data = {}

        print('Sending the result...')
        res = send_queue_result_dict(queue_item['uuid'], result_data)
        print()
        print('Completed.')

        deleted_input = delete_old_files(dir_path, max_hours=3)
        deleted = delete_old_files(os.path.join(dir_path, 'output', 'final_results'), max_hours=3)
        print('Deleted old files: ', deleted + deleted_input)

    else:
        print(f'Output file not found. Send error message - Processing error.')
        send_queue_error(queue_item['uuid'], 'Processing error. Please try again later.')
    print(str(datetime.datetime.now()))
    print('---------------------')
    return queue_item


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('d472139a-9f97-4496-8789-2505014154ad')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
