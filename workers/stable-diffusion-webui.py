import requests
import base64

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


def generate_image(prompt):
    url = 'http://127.0.0.1:7860'

    payload = {
        'prompt': prompt,
        'steps': 20,
        'width': 512,
        'height': 512
    }

    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    r = response.json()

    # with open("output.png", 'wb') as f:
    #     f.write(base64.b64decode(r['images'][0]))

    return 'data:image/png;base64,' + r['images'][0]


if __name__ == '__main__':
    queue_item = get_queue_next('c3a138bb-9b73-4543-8090-fc4f90e2bae8')
    if queue_item and 'uuid' in queue_item and 'data' in queue_item and 'prompt' in queue_item['data']:
        result = generate_image(queue_item['data']['prompt'])
        if result:
            res = send_queue_result(queue_item['uuid'], result)
            print(res)
    else:
        print('Queue is empty.')
