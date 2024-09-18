import requests


def webhook_post_result(webhook_url, queue_uuid, status, result_data):
    webhook_data = {
        'uuid': queue_uuid,
        'status': status,
        'result': result_data
    }
    webhook_resp = None
    try:
        r = requests.post(webhook_url, json=webhook_data, allow_redirects=True, timeout=60)
        webhook_resp = r.json()
    except Exception as e:
        print(str(e))
    return webhook_resp

