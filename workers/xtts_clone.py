import os
import sys
import time
import datetime
import subprocess
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.queue_manager import get_queue_next, send_queue_error
from utils.upload_file import upload_from_url
from utils.video_audio import cut_audio_duration

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_AUDIO_LENGTH = 30


def clone_voice_action(audio_file_path):
    voice_uuid = str(uuid.uuid4())

    result = subprocess.run([os.path.join(ROOT_DIR, 'workers', 'xtts_clone.sh'),
                             audio_file_path, voice_uuid], capture_output=True, text=True)

    print(result.stderr, result.stdout)

    return None


def processing(queue_item):
    print(queue_item)

    upload_dir_path = os.path.join(ROOT_DIR, 'uploads', 'xtts')
    if not queue_item or 'data' not in queue_item:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item

    audio_file_path = None

    if 'audio_file' in queue_item['data']:
        audio_url = queue_item['data']['audio_file']
        try:
            audio_file_path = upload_from_url(upload_dir_path, audio_url, type='audio')
            audio_file_path = cut_audio_duration(audio_file_path, MAX_AUDIO_LENGTH)
        except Exception as e:
            print(f'Error', str(e))

    if (not audio_file_path or not os.path.isfile(audio_file_path)):
        print('Send error message - Audio file not found.')
        send_queue_error(queue_item['uuid'], 'File not found.')
        return None

    print('Voice cloning...')
    voice_uuid = clone_voice_action(audio_file_path)

    if voice_uuid:
        print('voice_uuid', voice_uuid)
    else:
        print(f'Output is empty. Send error message - Processing error.')
        send_queue_error(queue_item['uuid'], 'Processing error. Please try again later.')


    print('---------------------')
    if 'pending' in queue_item:
        print('Pending:', queue_item['pending'])

    print(str(datetime.datetime.now()))
    print('---------------------')
    print('Wait 2 seconds...')
    time.sleep(2)


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('8e4c3fd1-452a-4911-8922-0d6eeb53426b')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
