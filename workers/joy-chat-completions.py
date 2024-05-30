import os
import subprocess
import sys
import time
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from utils.upload_to_gdrive import upload_and_share_file
from utils.upload_file import upload_from_url
from utils.queue_manager import get_queue_next, send_queue_error, send_queue_result

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# https://github.com/janhq/jan


def chat_completion(question):
    url = 'http://localhost:1337/v1/chat/completions'

    payload = {
        'messages': [{'content': question, 'role': 'user'}],
        'model': 'openchat-3.5-7b',
        'stream': False,
        'max_tokens': 2048,
        'frequency_penalty': 0,
        'presence_penalty': 0,
        'temperature': 0.7,
        'top_p': 0.95
    }

    res = None
    try:
        response = requests.post(url=url, json=payload)
        res = response.json()
    except Exception as e:
        print(str(e))

    if res is None:
        return None

    return res['choices'][0]['message']['content'].replace('<|end_of_turn|>', '') if 'choices' in res else None


def processing(queue_item):
    if not queue_item or 'data' not in queue_item:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item

    if 'question' not in queue_item['data']:
        print(f'Send error message - Bad data.')
        send_queue_error(queue_item['uuid'], 'Processing error. Bad data.')
        return queue_item

    print('---------------------')
    question = queue_item['data']['question']
    result = chat_completion(question)
    if result is not None:
        print('Question: ' + question)
        print('Answer: ' + result)
        res = send_queue_result(queue_item['uuid'], result)
        print('Completed.')
    else:
        print(f'Output is empty. Send error message - Processing error.')
        send_queue_error(queue_item['uuid'], 'Processing error. Please try again later.')

    print('---------------------')
    return queue_item


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('73a7044c-c24b-4fad-9a44-91e04d27f5b3')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
