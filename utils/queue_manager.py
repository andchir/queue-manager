import requests
import time


def get_queue_next(task_uuid):
    queue_url = 'https://queue.api2app.ru/queue_next/{}'.format(task_uuid)
    try:
        r = requests.get(url=queue_url)
    except Exception as e:
        print(str(e))
        return None
    return r.json() if r.status_code == 200 else None


def send_queue_result(queue_uuid, result_str, key='result'):
    queue_url = 'https://queue.api2app.ru/queue_result/{}'.format(queue_uuid)
    payload = {
        'result_data': dict(zip([key], [result_str]))
    }
    r = requests.post(url=queue_url, json=payload)
    return r.json()


def send_queue_result_dict(queue_uuid, result_dict):
    queue_url = 'https://queue.api2app.ru/queue_result/{}'.format(queue_uuid)
    payload = {
        'result_data': result_dict
    }
    r = requests.post(url=queue_url, json=payload)
    return r.json()


def send_queue_error(queue_uuid, message):
    queue_url = 'https://queue.api2app.ru/queue_error/{}'.format(queue_uuid)
    payload = {'message': message}
    r = requests.post(url=queue_url, data=payload)
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
