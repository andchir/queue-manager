#!/usr/bin/env python

import os
import sys
import uuid
import asyncio
import signal
import json
import websockets
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONNECTIONS: Dict[str, websockets.WebSocketServerProtocol] = {}

@dataclass
class WebSocketMessage:
    recipient_uuid: Optional[str] = None
    message: Optional[str] = None


async def register(websocket):
    tmp_uuid = str(uuid.uuid4())
    logger.info(f'New connection: {tmp_uuid}')
    CONNECTIONS[f'tmp_{tmp_uuid}'] = websocket
    logger.info(f'Connections total: {len(CONNECTIONS)}')

    try:
        await websocket.send('..:: Hello from the Notification Center ::..')
        async for message in websocket:
            try:
                event = json.loads(message) if message.startswith('{') else WebSocketMessage(message=message)

                if isinstance(event, dict):
                    event = WebSocketMessage(**event)

                if event.message == 'connected' and event.recipient_uuid:
                    logger.info(f'Set UUID: {event.recipient_uuid}')
                    CONNECTIONS[event.recipient_uuid] = websocket
                    del CONNECTIONS[f'tmp_{tmp_uuid}']
                else:
                    logger.info(f'Message: {event}')
                    if event.recipient_uuid and event.recipient_uuid in CONNECTIONS:
                        await CONNECTIONS[event.recipient_uuid].send(event.message)
                    else:
                        logger.warning(f'Connection not found for UUID: {event.recipient_uuid}')
            except json.JSONDecodeError as e:
                logger.error(f'JSON decode error: {e}')
            except Exception as e:
                logger.error(f'Error processing message: {e}')

    finally:
        logger.info(f'Disconnected: {tmp_uuid}')
        if f'tmp_{tmp_uuid}' in CONNECTIONS:
            del CONNECTIONS[f'tmp_{tmp_uuid}']
        else:
            for key, con in CONNECTIONS.items():
                if con == websocket:
                    del CONNECTIONS[key]
                    break
        logger.info(f'Connections total: {len(CONNECTIONS)}')


async def main(port=8765):
    logger.info('Starting WebSocket server')

    # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with websockets.serve(
        register,
        host='',
        port=port,
        reuse_port=True,
        ping_interval=60,
        ping_timeout=90
    ):
        await stop  # Waiting for SIGTERM signal to terminate


if __name__ == "__main__":
    args = sys.argv[1:]
    port_num = args[0] if len(args) > 0 else 8765
    asyncio.run(main(port=port_num))
