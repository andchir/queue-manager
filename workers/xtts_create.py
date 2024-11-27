import datetime
import os
import sys
import time
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.upload_to_yadisk import upload_and_share_file
from utils.queue_manager import get_queue_next, send_queue_error, send_queue_result_dict
from utils.upload_file import upload_from_url, delete_old_files
from utils.video_audio import cut_audio_duration

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_tts_audio(text, language, voice, uuid=''):

    upload_dir_path = os.path.join(ROOT_DIR, 'uploads', 'xtts_output')
    output_file_path = os.path.join(upload_dir_path, 'output_' + uuid + '.wav')

    result = subprocess.run([os.path.join(ROOT_DIR, 'workers', 'xtts_create.sh'),
                             text, language, voice, output_file_path], capture_output=True, text=True)

    print(result.stdout)

    if 'Done.' in result.stdout:
        return output_file_path

    return None


def processing(queue_item):
    data = queue_item['data']['input'] if queue_item['data'] is not None and 'input' in queue_item['data'] else {}
    text = data['text'] if 'text' in data else ''
    language = data['language'] if 'language' in data else 'en'
    voice = data['voice'] if 'voice' in data else 'Claribel Dervla'
    speaker_name = data['speaker_name'] if 'speaker_name' in data else None

    task_uuid = queue_item['uuid'] if 'uuid' in queue_item else ''
    upload_dir_path = os.path.join(ROOT_DIR, 'uploads', 'xtts_output')

    if speaker_name and type(speaker_name) is str:
        clone_file_path = os.path.join(
            '/media/andrew/256GB/python_projects/coqui-ai-TTS',
            'demo_outputs', 'cloned_speakers', speaker_name + '.json'
        )
        if not os.path.exists(clone_file_path):
            print('Voice not found. Send error message.')
            send_queue_error(queue_item['uuid'], 'Voice not found.')
            return
        else:
            voice = speaker_name

    print('---------------------')
    print('Creating TTS audio...')
    file_path = create_tts_audio(text, language, voice, task_uuid)

    if file_path and os.path.isfile(file_path):
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
    else:
        print(f'Output is empty. Send error message - Processing error.')
        send_queue_error(queue_item['uuid'], 'Processing error. Please try again later.')

    deleted_input = delete_old_files(upload_dir_path, max_hours=2)
    print('Deleted old files: ', deleted_input)

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
        queue_item = get_queue_next('91872ce5-0bfe-4f9e-a251-d640f3d1c39a')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
