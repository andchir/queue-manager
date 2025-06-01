import requests
from config import settings


def send_message_to_bot(message, max_length=3584):
    bot_token = settings.tg_bot_token
    chat_id = settings.tg_chat_id
    if not bot_token or not chat_id:
        return None

    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    responses = []

    for i in range(0, len(message), max_length):
        chunk = message[i:i + max_length]
        payload = {
            'chat_id': chat_id,
            'text': chunk
        }
        try:
            response = requests.post(url, json=payload)
            responses.append(response.json())
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

    return responses[-1] if responses else None
