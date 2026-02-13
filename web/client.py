#!/usr/bin/env python

import sys
import os
import json
import asyncio
import websockets

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings


async def send_message(recipient_uuid, message):
    uri = f'ws://localhost:{settings.ws_port}'
    async with websockets.connect(uri) as websocket:
        data = {'recipient_uuid': recipient_uuid, 'message': message}

        await websocket.send(json.dumps(data))
        print('Send:', data)


def ws_send_message(recipient_uuid, message):
    asyncio.run(send_message(recipient_uuid, message))


if __name__ == "__main__":
    recipient_uuid = sys.argv[1] if len(sys.argv) > 1 else None
    message = sys.argv[2] if len(sys.argv) > 2 else 'Hello.'
    if recipient_uuid is not None:
        asyncio.run(send_message(recipient_uuid, message))
    else:
        print('Usage: client.py <recipient_uuid> <message>')
