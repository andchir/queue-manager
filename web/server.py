#!/usr/bin/env python

import uuid
import asyncio
import json
import websockets

CONNECTIONS = {}


async def register(websocket):
    tmp_uuid = str(uuid.uuid1())
    print('New connection', tmp_uuid)
    CONNECTIONS['tmp_' + tmp_uuid] = websocket
    print('Connections total:', len(CONNECTIONS))
    await websocket.send('..:: Hello from the Notification Center ::..')
    try:
        async for message in websocket:
            event = json.loads(message)
            recipient_uuid = event['recipient_uuid'] if 'recipient_uuid' in event else None
            message = event['message'] if 'message' in event else ''
            if message == 'connected' and recipient_uuid:
                print('Set UUID:', recipient_uuid)
                CONNECTIONS[recipient_uuid] = websocket
                del CONNECTIONS['tmp_' + tmp_uuid]
            else:
                print('Message', event)
                if recipient_uuid is not None and recipient_uuid in CONNECTIONS:
                    await CONNECTIONS[recipient_uuid].send(message)
    finally:
        print('Disconnected', tmp_uuid)
        if 'tmp_' + tmp_uuid in CONNECTIONS:
            del CONNECTIONS['tmp_' + tmp_uuid]
        else:
            for key, con in CONNECTIONS.items():
                if con == websocket:
                    del CONNECTIONS[key]
                    break
        print('Connections total:', len(CONNECTIONS))


async def main():
    print('Starting WebSocket server')
    async with websockets.serve(register, 'localhost', 8765):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
