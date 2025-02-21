import requests
from config import settings


def send_message_to_bot(message):
    bot_token = settings.tg_bot_token
    chat_id = settings.tg_chat_id
    if not bot_token or not chat_id:
        return None

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, json=payload)
    return response.json()
