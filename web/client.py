#!/usr/bin/env python

import sys
import os
import json
import asyncio
import websockets
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def send_message(recipient_uuid, message):
    uri = f'ws://localhost:{settings.ws_port}'
    try:
        async with websockets.connect(uri) as websocket:
            data = {'recipient_uuid': recipient_uuid, 'message': message}
            await websocket.send(json.dumps(data))
            logger.info(f'Message sent to {recipient_uuid}: {message}')
    except websockets.exceptions.WebSocketException as e:
        logger.error(f'WebSocket connection error for {recipient_uuid}: {e}')
    except Exception as e:
        logger.error(f'Unexpected error sending message to {recipient_uuid}: {e}', exc_info=True)


def ws_send_message(recipient_uuid, message):
    asyncio.run(send_message(recipient_uuid, message))


if __name__ == "__main__":
    recipient_uuid = sys.argv[1] if len(sys.argv) > 1 else None
    message = sys.argv[2] if len(sys.argv) > 2 else 'Hello.'
    if recipient_uuid is not None:
        asyncio.run(send_message(recipient_uuid, message))
    else:
        print('Usage: client.py <recipient_uuid> <message>')
