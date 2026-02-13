#!/usr/bin/env python

import sys
import uuid
import asyncio
import signal
import json
import logging
from typing import Dict, Optional
from dataclasses import dataclass

from websockets.asyncio.server import serve, ServerConnection

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Forward mapping: key (UUID or tmp_UUID) -> websocket
CONNECTIONS: Dict[str, ServerConnection] = {}
# Reverse mapping: websocket id -> key, for O(1) cleanup on disconnect
WS_TO_KEY: Dict[int, str] = {}


@dataclass
class WebSocketMessage:
    recipient_uuid: Optional[str] = None
    message: Optional[str] = None


def _add_connection(key: str, websocket) -> None:
    """Register a connection with both forward and reverse mappings."""
    CONNECTIONS[key] = websocket
    WS_TO_KEY[id(websocket)] = key


def _remove_connection_by_key(key: str) -> None:
    """Remove a connection by its key from both mappings."""
    ws = CONNECTIONS.pop(key, None)
    if ws is not None:
        WS_TO_KEY.pop(id(ws), None)


def _remove_connection_by_ws(websocket) -> None:
    """Remove a connection by websocket reference using O(1) reverse lookup."""
    key = WS_TO_KEY.pop(id(websocket), None)
    if key is not None:
        CONNECTIONS.pop(key, None)


def _parse_message(message: str) -> WebSocketMessage:
    """Parse an incoming WebSocket message into a WebSocketMessage."""
    if not message.startswith('{'):
        return WebSocketMessage(message=message)
    data = json.loads(message)
    if isinstance(data, dict):
        return WebSocketMessage(**data)
    return WebSocketMessage(message=message)


async def register(websocket):
    tmp_uuid = str(uuid.uuid4())
    tmp_key = f'tmp_{tmp_uuid}'
    logger.info(f'New connection: {tmp_uuid}')
    _add_connection(tmp_key, websocket)
    logger.info(f'Connections total: {len(CONNECTIONS)}')

    try:
        await websocket.send('..:: Hello from the Notification Center ::..')
        async for message in websocket:
            try:
                event = _parse_message(message)

                if event.message == 'connected' and event.recipient_uuid:
                    logger.info(f'Set UUID: {event.recipient_uuid}')
                    _remove_connection_by_key(tmp_key)
                    _add_connection(event.recipient_uuid, websocket)
                else:
                    logger.info(f'Message: {event}')
                    recipient_ws = CONNECTIONS.get(event.recipient_uuid) if event.recipient_uuid else None
                    if recipient_ws is not None:
                        await recipient_ws.send(event.message)
                    else:
                        logger.warning(f'Connection not found for UUID: {event.recipient_uuid}')
            except json.JSONDecodeError as e:
                logger.error(f'JSON decode error: {e}')
            except Exception as e:
                logger.error(f'Error processing message: {e}')

    finally:
        logger.info(f'Disconnected: {tmp_uuid}')
        _remove_connection_by_ws(websocket)
        logger.info(f'Connections total: {len(CONNECTIONS)}')


async def main(port=8765):
    logger.info('Starting WebSocket server')

    # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with serve(
        register,
        host='',
        port=port,
        reuse_port=True,
        ping_interval=60,
        ping_timeout=30
    ):
        await stop  # Waiting for SIGTERM signal to terminate


# ASGI application for uvicorn compatibility
async def app(scope, receive, send):
    """
    ASGI-compatible WebSocket application.

    This allows running the WebSocket server with uvicorn:
        uvicorn web.server:app --port 8765

    or with gunicorn:
        gunicorn -k uvicorn.workers.UvicornWorker web.server:app --bind 0.0.0.0:8765
    """
    if scope['type'] == 'websocket':
        await websocket_handler(scope, receive, send)
    else:
        # Return 404 for non-WebSocket requests
        await send({
            'type': 'http.response.start',
            'status': 404,
            'headers': [[b'content-type', b'text/plain']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'WebSocket endpoint only',
        })


async def websocket_handler(scope, receive, send):
    """Handle a single WebSocket connection using ASGI protocol."""
    # Wait for connection
    message = await receive()
    if message['type'] != 'websocket.connect':
        return

    # Accept the connection
    await send({'type': 'websocket.accept'})

    tmp_uuid = str(uuid.uuid4())
    tmp_key = f'tmp_{tmp_uuid}'
    logger.info(f'New ASGI connection: {tmp_uuid}')

    # Create a pseudo-websocket object to work with existing register logic
    class ASGIWebSocket:
        def __init__(self, scope, receive, send):
            self.scope = scope
            self._receive = receive
            self._send = send
            self._closed = False

        async def send(self, message: str):
            """Send a text message to the client."""
            if not self._closed:
                await self._send({
                    'type': 'websocket.send',
                    'text': message
                })

        async def __aiter__(self):
            """Async iterator for receiving messages."""
            return self

        async def __anext__(self):
            """Receive the next message."""
            if self._closed:
                raise StopAsyncIteration

            message = await self._receive()
            if message['type'] == 'websocket.disconnect':
                self._closed = True
                raise StopAsyncIteration
            elif message['type'] == 'websocket.receive':
                return message.get('text', message.get('bytes', ''))
            else:
                raise StopAsyncIteration

    websocket = ASGIWebSocket(scope, receive, send)
    _add_connection(tmp_key, websocket)
    logger.info(f'Connections total: {len(CONNECTIONS)}')

    try:
        await websocket.send('..:: Hello from the Notification Center ::..')
        async for message in websocket:
            try:
                event = _parse_message(message)

                if event.message == 'connected' and event.recipient_uuid:
                    logger.info(f'Set UUID: {event.recipient_uuid}')
                    _remove_connection_by_key(tmp_key)
                    _add_connection(event.recipient_uuid, websocket)
                else:
                    logger.info(f'Message: {event}')
                    recipient_ws = CONNECTIONS.get(event.recipient_uuid) if event.recipient_uuid else None
                    if recipient_ws is not None:
                        await recipient_ws.send(event.message)
                    else:
                        logger.warning(f'Connection not found for UUID: {event.recipient_uuid}')
            except json.JSONDecodeError as e:
                logger.error(f'JSON decode error: {e}')
            except Exception as e:
                logger.error(f'Error processing message: {e}')

    finally:
        logger.info(f'Disconnected: {tmp_uuid}')
        _remove_connection_by_ws(websocket)
        logger.info(f'Connections total: {len(CONNECTIONS)}')


if __name__ == "__main__":
    args = sys.argv[1:]
    port_num = args[0] if len(args) > 0 else 8765
    asyncio.run(main(port=port_num))
