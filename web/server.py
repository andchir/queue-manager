#!/usr/bin/env python

import os
import sys
import uuid
import asyncio
import signal
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
            event = json.loads(message) if message.startswith('{') else message
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
                else:
                    print(recipient_uuid, 'Connection not found.')
                    print()
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


async def main(port=8765):
    print('Starting WebSocket server')

    # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with websockets.serve(register, host='', port=port, reuse_port=True):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    args = sys.argv[1:]
    port_num = args[0] if len(args) > 0 else 8765
    asyncio.run(main(port=port_num))
