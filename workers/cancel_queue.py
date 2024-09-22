import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.queue_manager import get_queue_next, send_queue_error


def processing(queue_item):
    print('---------------------')
    if 'pending' in queue_item:
        print('Pending:', queue_item['pending'])

    print('Send error message...')
    send_queue_error(queue_item['uuid'], 'Please upload image file.')
    print('---------------------')


if __name__ == '__main__':
    show_message = True
    while True:
        queue_item = get_queue_next('304a0d98-216b-45d2-bf63-56811e49ab6b')
        if queue_item is not None:
            processing(queue_item)
            show_message = True
        else:
            if show_message:
                print('Waiting for a task...')
                show_message = False
            time.sleep(10)
