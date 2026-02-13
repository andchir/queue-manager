#!/usr/bin/env python

import sys
import uuid
import asyncio
import signal
import json
import logging
from typing import Dict, Optional
from dataclasses import dataclass

import redis.asyncio as redis
from websockets.asyncio.server import serve, ServerConnection

try:
    from config import settings
    REDIS_HOST = settings.redis_host
    REDIS_PORT = settings.redis_port
    REDIS_DB = settings.redis_db
except ImportError:
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

KEY_PREFIX = 'ws:conn:'
KEY_TO_WS_PREFIX = 'ws:key_to_ws:'
WS_TO_KEY_PREFIX = 'ws:ws_to_key:'

PUB_CHANNEL = 'ws:messages'


class RedisConnectionManager:
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT, db: int = REDIS_DB):
        self.redis: Optional[redis.Redis] = None
        self.host = host
        self.port = port
        self.db = db
        self.local_connections: Dict[str, ServerConnection] = {}
        self.local_ws_to_key: Dict[int, str] = {}
        self.pubsub: Optional[redis.client.PubSub] = None
        self.pubsub_task: Optional[asyncio.Task] = None

    async def connect(self):
        self.redis = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        await self.redis.ping()
        logger.info(f'Connected to Redis at {self.host}:{self.port}')

    async def disconnect(self):
        if self.pubsub_task:
            self.pubsub_task.cancel()
            try:
                await self.pubsub_task
            except asyncio.CancelledError:
                pass
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

    def _get_redis_key(self, key: str) -> str:
        return f'{KEY_PREFIX}{key}'

    def _get_key_to_ws_key(self, key: str) -> str:
        return f'{KEY_TO_WS_PREFIX}{key}'

    def _get_ws_to_key_key(self, ws_id: int) -> str:
        return f'{WS_TO_KEY_PREFIX}{ws_id}'

    async def add_connection(self, key: str, websocket: ServerConnection) -> None:
        ws_id = id(websocket)
        self.local_connections[key] = websocket
        self.local_ws_to_key[ws_id] = key

        if self.redis:
            await self.redis.set(self._get_key_to_ws_key(key), str(ws_id))
            await self.redis.set(self._get_ws_to_key_key(ws_id), key)

    async def remove_connection_by_key(self, key: str) -> None:
        ws_id = None
        if key in self.local_connections:
            ws_id = id(self.local_connections[key])
            del self.local_connections[key]

        if self.redis:
            ws_id_str = await self.redis.get(self._get_key_to_ws_key(key))
            if ws_id_str:
                ws_id = int(ws_id_str)
            await self.redis.delete(self._get_key_to_ws_key(key))
            if ws_id:
                await self.redis.delete(self._get_ws_to_key_key(ws_id))

    async def remove_connection_by_websocket(self, websocket) -> None:
        ws_id = id(websocket)
        key = self.local_ws_to_key.pop(ws_id, None)
        if key and key in self.local_connections:
            del self.local_connections[key]

        if self.redis:
            key = await self.redis.get(self._get_ws_to_key_key(ws_id))
            await self.redis.delete(self._get_ws_to_key_key(ws_id))
            if key:
                await self.redis.delete(self._get_key_to_ws_key(key))

    def get_local_websocket(self, key: str) -> Optional[ServerConnection]:
        return self.local_connections.get(key)

    async def get_redis_websocket_id(self, key: str) -> Optional[str]:
        if self.redis:
            return await self.redis.get(self._get_key_to_ws_key(key))
        return None

    async def publish_message(self, recipient_key: str, message: str) -> None:
        if self.redis:
            await self.redis.publish(PUB_CHANNEL, json.dumps({
                'recipient_key': recipient_key,
                'message': message
            }))

    async def subscribe(self):
        await self.pubsub.subscribe(PUB_CHANNEL)
        self.pubsub_task = asyncio.create_task(self._handle_pubsub())

    async def _handle_pubsub(self):
        try:
            async for message in self.pubsub:
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        recipient_key = data.get('recipient_key')
                        message_text = data.get('message')
                        if recipient_key and message_text:
                            ws = self.local_connections.get(recipient_key)
                            if ws:
                                await ws.send(message_text)
                    except json.JSONDecodeError as e:
                        logger.error(f'JSON decode error from Redis: {e}')
        except asyncio.CancelledError:
            pass


conn_manager: Optional[RedisConnectionManager] = None


@dataclass
class WebSocketMessage:
    recipient_uuid: Optional[str] = None
    message: Optional[str] = None


def _parse_message(message: str) -> WebSocketMessage:
    if not message.startswith('{'):
        return WebSocketMessage(message=message)
    data = json.loads(message)
    if isinstance(data, dict):
        return WebSocketMessage(**data)
    return WebSocketMessage(message=message)


async def register(websocket):
    global conn_manager
    if not conn_manager:
        conn_manager = RedisConnectionManager()
        await conn_manager.connect()
        await conn_manager.subscribe()

    tmp_uuid = str(uuid.uuid4())
    tmp_key = f'tmp_{tmp_uuid}'
    logger.info(f'New connection: {tmp_uuid}')

    # Add connection to local registry first (fast, synchronous operation)
    ws_id = id(websocket)
    conn_manager.local_connections[tmp_key] = websocket
    conn_manager.local_ws_to_key[ws_id] = tmp_key
    logger.info(f'Connections total: {len(conn_manager.local_connections)}')

    # Store in Redis asynchronously after adding to local registry
    async def _store_in_redis():
        if conn_manager.redis:
            try:
                await conn_manager.redis.set(conn_manager._get_key_to_ws_key(tmp_key), str(ws_id))
                await conn_manager.redis.set(conn_manager._get_ws_to_key_key(ws_id), tmp_key)
            except Exception as e:
                logger.error(f'Redis storage error: {e}')

    asyncio.create_task(_store_in_redis())

    try:
        await websocket.send('..:: Hello from the Notification Center (Redis) ::..')
        async for message in websocket:
            try:
                event = _parse_message(message)

                if event.message == 'connected' and event.recipient_uuid:
                    logger.info(f'Set UUID: {event.recipient_uuid}')
                    await conn_manager.remove_connection_by_key(tmp_key)
                    await conn_manager.add_connection(event.recipient_uuid, websocket)
                else:
                    logger.info(f'Message: {event}')
                    recipient_ws = conn_manager.get_local_websocket(event.recipient_uuid) if event.recipient_uuid else None
                    if recipient_ws is not None:
                        await recipient_ws.send(event.message)
                    else:
                        await conn_manager.publish_message(event.recipient_uuid, event.message)
                        logger.info(f'Message published to Redis for: {event.recipient_uuid}')
            except json.JSONDecodeError as e:
                logger.error(f'JSON decode error: {e}')
            except Exception as e:
                logger.error(f'Error processing message: {e}')

    finally:
        logger.info(f'Disconnected: {tmp_uuid}')
        await conn_manager.remove_connection_by_websocket(websocket)
        logger.info(f'Connections total: {len(conn_manager.local_connections)}')


async def main(port=8766):
    global conn_manager
    logger.info('Starting Redis WebSocket server')

    conn_manager = RedisConnectionManager()
    await conn_manager.connect()
    await conn_manager.subscribe()

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
        await stop

    await conn_manager.disconnect()


async def app(scope, receive, send):
    global conn_manager
    if not conn_manager:
        conn_manager = RedisConnectionManager()
        await conn_manager.connect()
        await conn_manager.subscribe()

    if scope['type'] == 'websocket':
        await websocket_handler(scope, receive, send)
    else:
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
    global conn_manager
    if not conn_manager:
        conn_manager = RedisConnectionManager()
        await conn_manager.connect()
        await conn_manager.subscribe()

    message = await receive()
    if message['type'] != 'websocket.connect':
        return

    await send({'type': 'websocket.accept'})

    tmp_uuid = str(uuid.uuid4())
    tmp_key = f'tmp_{tmp_uuid}'
    logger.info(f'New ASGI connection: {tmp_uuid}')

    class ASGIWebSocket:
        def __init__(self, scope, receive, send):
            self.scope = scope
            self._receive = receive
            self._send = send
            self._closed = False

        async def send(self, message: str):
            if not self._closed:
                await self._send({
                    'type': 'websocket.send',
                    'text': message
                })

        def __aiter__(self):
            return self

        async def __anext__(self):
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

    # Add connection to local registry first (fast, synchronous operation)
    ws_id = id(websocket)
    conn_manager.local_connections[tmp_key] = websocket
    conn_manager.local_ws_to_key[ws_id] = tmp_key
    logger.info(f'Connections total: {len(conn_manager.local_connections)}')

    # Store in Redis asynchronously after adding to local registry
    async def _store_in_redis():
        if conn_manager.redis:
            try:
                await conn_manager.redis.set(conn_manager._get_key_to_ws_key(tmp_key), str(ws_id))
                await conn_manager.redis.set(conn_manager._get_ws_to_key_key(ws_id), tmp_key)
            except Exception as e:
                logger.error(f'Redis storage error: {e}')

    asyncio.create_task(_store_in_redis())

    try:
        await websocket.send('..:: Hello from the Notification Center (Redis) ::..')
        async for message in websocket:
            try:
                event = _parse_message(message)

                if event.message == 'connected' and event.recipient_uuid:
                    logger.info(f'Set UUID: {event.recipient_uuid}')
                    await conn_manager.remove_connection_by_key(tmp_key)
                    await conn_manager.add_connection(event.recipient_uuid, websocket)
                else:
                    logger.info(f'Message: {event}')
                    recipient_ws = conn_manager.get_local_websocket(event.recipient_uuid) if event.recipient_uuid else None
                    if recipient_ws is not None:
                        await recipient_ws.send(event.message)
                    else:
                        await conn_manager.publish_message(event.recipient_uuid, event.message)
                        logger.info(f'Message published to Redis for: {event.recipient_uuid}')
            except json.JSONDecodeError as e:
                logger.error(f'JSON decode error: {e}')
            except Exception as e:
                logger.error(f'Error processing message: {e}')

    finally:
        logger.info(f'Disconnected: {tmp_uuid}')
        await conn_manager.remove_connection_by_websocket(websocket)
        logger.info(f'Connections total: {len(conn_manager.local_connections)}')


if __name__ == "__main__":
    args = sys.argv[1:]
    port_num = args[0] if len(args) > 0 else 8766
    asyncio.run(main(port=port_num))
