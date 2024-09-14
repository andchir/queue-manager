import datetime
import json
import os
from typing import Union
import requests
import codecs

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status, UploadFile, Form, Body
from sqlalchemy.exc import NoResultFound

from db.db import session_maker
from models.queue import QueueStatus
from repositories.proxy_repository import ProxyRepository
from repositories.queue_repository import QueueRepository
from repositories.tasks_repository import TasksRepository
from schemas.proxy_schema import ProxySchema, ProxyAddSchema
from schemas.queue_schema import QueueAddSchema, QueueUpdateSchema, QueueSchema, QueueResultSchema
from schemas.response import DataResponseSuccess, ResponseTasksItems, ResponseItemId, ResponseQueueItems, \
    ResponseItemUuid, ResponseProxyItems
from schemas.task_schema import TaskAddSchema, TaskUpdateSchema, TaskSchema, TaskDetailedSchema
from utils.restore_outdated_queue_items import restore_outdated_queue_items
from utils.security import check_authentication_header
from utils.upload_file import upload_file, delete_old_files
from utils.webhook import webhook_post_result
from config import settings
from web.client import send_message

router = APIRouter()
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


@router.get('/')
def read_root():
    return {'Hello': 'World'}


@router.post('/tasks', name='Create Task', tags=['Tasks'],
             dependencies=[Depends(check_authentication_header)])
def create_task_action(task: TaskAddSchema) -> Union[ResponseItemId, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        task = task_repository.add_one(task.model_dump())

    return {
        'success': True,
        'item_id': task.id,
        'item_uuid': task.uuid
    }


@router.patch('/tasks/{task_id}', name='Update Task', tags=['Tasks'],
              dependencies=[Depends(check_authentication_header)])
def update_task_action(task: TaskUpdateSchema, task_id: int) -> Union[TaskSchema, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        try:
            res = task_repository.update_one(task.model_dump(exclude_unset=True), task_id)
        except NoResultFound:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item with ID {task_id} not found.')

    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item with ID {task_id} not found.')

    return res


@router.get('/tasks/{task_id}', name='View task', tags=['Tasks'],
            dependencies=[Depends(check_authentication_header)])
def get_task_action(task_id: int) -> Union[TaskDetailedSchema, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        res = task_repository.find_one(task_id)

    if res is not None:
        return res
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Task with ID {task_id} not found.')


@router.get('/tasks', name='Tasks list', tags=['Tasks'],
            dependencies=[Depends(check_authentication_header)],
            response_model=ResponseTasksItems)
def get_tasks_list_action() -> Union[ResponseTasksItems, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        res = task_repository.find_all()

    return {
        'items': res
    }


@router.delete('/tasks/{task_id}', name='Delete task', tags=['Tasks'],
               dependencies=[Depends(check_authentication_header)],
               response_model=DataResponseSuccess)
def delete_task_action(task_id: int) -> Union[DataResponseSuccess, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        rowcount = task_repository.delete(task_id)

    if rowcount > 0:
        return {
            'success': True
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item with ID {task_id} not found.')


@router.post('/queue/{task_uuid}', name='Create Queue Item', tags=['Queue'],
             dependencies=[Depends(check_authentication_header)])
async def create_queue_action(
        request: Request,
        task_uuid: str,
        data: str = Form(None),
        image_file: UploadFile = None,
        image_file2: UploadFile = None,
        video_file: UploadFile = None,
        audio_file: UploadFile = None
) -> Union[ResponseItemUuid, dict]:

    if data and data.startswith('{'):
        data = json.loads(data)
    else:
        data = {'data': {'input': data}}

    if 'data' not in data:
        data['data'] = data.copy()
        if 'owner' in data['data']:
            del data['data']['owner']
    if 'owner' not in data:
        data['owner'] = ''

    try:
        payload = await request.json()
        if payload:
            data['data'].update(payload)
    except Exception as e:
        print(str(e))

    upload_dir_path = os.path.join(ROOT_DIR, 'uploads')
    base_url = f'{request.url.scheme}://{request.url.hostname}'
    if request.url.port is not None and request.url.port != 80:
        base_url += f':{request.url.port}'

    restore_outdated_queue_items()
    delete_old_files(upload_dir_path)

    if image_file is not None:
        file_name = upload_file(image_file, upload_dir_path, type='image')
        if file_name:
            data['data']['image_file'] = f'{base_url}/uploads/{file_name}'

    if image_file2 is not None:
        file_name = upload_file(image_file2, upload_dir_path, type='image')
        if file_name:
            data['data']['image_file2'] = f'{base_url}/uploads/{file_name}'

    if video_file is not None:
        file_name = upload_file(video_file, upload_dir_path, type='video')
        if file_name:
            data['data']['video_file'] = f'{base_url}/uploads/{file_name}'

    if audio_file is not None:
        file_name = upload_file(audio_file, upload_dir_path, type='audio')
        if file_name:
            data['data']['audio_file'] = f'{base_url}/uploads/{file_name}'

    item_uuid = None
    if 'uid' in data['data'] or 'uuid' in data['data']:
        item_uuid = data['data']['uid'] if 'uid' in data['data'] else data['data']['uuid']

    with session_maker() as session:
        task_repository = TasksRepository(session)
        task = task_repository.find_one_by_uuid(task_uuid)

        if task is not None:
            queue_item_new = QueueAddSchema(status=QueueStatus.PENDING.value, task_id=task.id, **data)
            queue_repository = QueueRepository(session)
            queue_item = queue_repository.add_one(queue_item_new.model_dump(), item_uuid=item_uuid)
            return {
                'success': True if queue_item is not None else False,
                'uuid': queue_item.uuid if queue_item is not None else None,
                'url': f'{base_url}/queue/{queue_item.uuid}'
                if queue_item is not None else None
            }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Task with UUID {task_uuid} not found.')


@router.get('/queue', name='Queue list', tags=['Queue'],
            dependencies=[Depends(check_authentication_header)],
            response_model=ResponseQueueItems)
def get_queue_list_action(task_id: int = None, task_uuid: str = None) -> Union[ResponseQueueItems, dict]:
    with session_maker() as session:
        if task_uuid is not None:
            task_repository = TasksRepository(session)
            task = task_repository.find_one_by_uuid(task_uuid)
            task_id = task.id
        queue_repository = QueueRepository(session)
        res = queue_repository.find_all(limit=100, filter={'task_id': task_id} if task_id else None)

    return {
        'items': res
    }


@router.get('/queue/{uuid}', name='Get Queue Item State', tags=['Queue'])
            # dependencies=[Depends(check_authentication_header)])
def get_queue_action(uuid: str) -> Union[QueueSchema, dict]:
    with session_maker() as session:
        queue_repository = QueueRepository(session)
        queue_item = queue_repository.find_one_by_uuid(uuid)
        if queue_item is not None:
            queue_repository = QueueRepository(session)
            queue_list = queue_repository.find_by_status(QueueStatus.PENDING.value, task_id=queue_item.task_id)
            queue_index = next((index for (index, d) in enumerate(list(queue_list)) if d[0].uuid == uuid), None)

            result = queue_item.to_read_model()
            result.number = queue_index + 1 if queue_index is not None else 0
            return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Task not found.')


@router.get('/queue_next/{task_uuid}', name='Get Next Queue Item', tags=['Queue'])
def get_queue_next_action(task_uuid: str, user_ip: str = Header(None, alias='X-Real-IP')) -> Union[QueueSchema, dict]:

    restore_outdated_queue_items()

    with session_maker() as session:
        task_repository = TasksRepository(session)
        task = task_repository.find_one_by_uuid(task_uuid)

        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Task not found.')

        queue_repository = QueueRepository(session)
        res = queue_repository.find_one_next(task.id)
        if res is not None:
            queue_item = res[0]
            result = queue_repository.update_one({
                'owner': user_ip if user_ip is not None else '',
                'status': QueueStatus.PROCESSING.value,
                'time_updated': datetime.datetime.utcnow()
            }, queue_item.id)

            queue_list = queue_repository.find_by_status(QueueStatus.PENDING.value, task_id=task.id)
            result.pending = len(list(queue_list))

            return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item not found.')


@router.post('/queue_result/{uuid}', name='Send Queue Item result', tags=['Queue'])
async def set_queue_result_action(request: Request, queue_item: QueueResultSchema, uuid: str) -> Union[QueueSchema, dict]:

    try:
        payload = await request.json()
    except Exception as e:
        print(str(e))
        payload = None

    restore_outdated_queue_items()

    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_by_uuid_and_status(uuid, [
            QueueStatus.PENDING.value,
            QueueStatus.PROCESSING.value,
            QueueStatus.COMPLETED.value
        ])

        result_data = queue_item.result_data if hasattr(queue_item, 'result_data') else None
        if result_data is None and payload is not None:
            result_data = payload

        result_status = QueueStatus.COMPLETED.value if 'code' not in result_data or result_data['code'] == 200 \
            else QueueStatus.PROCESSING.value

        if res is not None:
            result = queue_repository.update_one({
                'status': result_status,
                'result_data': result_data,
                'time_updated': datetime.datetime.utcnow()
            }, res.id)

            if result:
                task_id = result.task_id
                task_repository = TasksRepository(session)
                task = task_repository.find_one(task_id)
                if task and task.webhook_url:
                    webhook_resp = webhook_post_result(task.webhook_url, uuid, result.status, result.result_data)
                    # print(webhook_resp)
                # send WebSocker message
                if settings.ws_enabled == 'true':
                    await send_message(result.uuid, json.dumps(result_data))

            return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item not found.')


@router.post('/queue_error/{uuid}', name='Send Queue Item error', tags=['Queue'])
def set_queue_result_action(uuid: str, message: str = Form()) -> Union[QueueSchema, dict]:
    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_by_uuid_and_status(uuid, [QueueStatus.PENDING.value, QueueStatus.PROCESSING.value])

        if res is not None:
            result = queue_repository.update_one({
                'status': QueueStatus.ERROR.value,
                'result_data': {'message': message},
                'time_updated': datetime.datetime.utcnow()
            }, res.id)

            if result:
                task_id = result.task_id
                task_repository = TasksRepository(session)
                task = task_repository.find_one(task_id)
                if task and task.webhook_url:
                    webhook_resp = webhook_post_result(task.webhook_url, uuid, result.status, result.result_data)
                    # print(webhook_resp)

        return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item not found.')


@router.post('/proxy', name='Create Proxy Item', tags=['Proxy'],
             dependencies=[Depends(check_authentication_header)])
def create_proxy_action(proxy: ProxyAddSchema) -> Union[ResponseItemId, dict]:
    with session_maker() as session:
        proxy_repository = ProxyRepository(session)
        proxy = proxy_repository.add_one(proxy.model_dump())

    return {
        'success': True,
        'item_id': proxy.id,
        'item_uuid': proxy.uuid
    }


@router.get('/proxy', name='Proxy list', tags=['Proxy'],
            dependencies=[Depends(check_authentication_header)],
            response_model=ResponseProxyItems)
def get_proxy_list_action() -> Union[ResponseProxyItems, dict]:
    with session_maker() as session:
        proxy_repository = ProxyRepository(session)
        res = proxy_repository.find_all()

    return {
        'items': res
    }


@router.delete('/proxy/{proxy_id}', name='Delete proxy', tags=['Proxy'],
               dependencies=[Depends(check_authentication_header)],
               response_model=DataResponseSuccess)
def delete_proxy_action(item_id: int) -> Union[DataResponseSuccess, dict]:
    with session_maker() as session:
        repository = ProxyRepository(session)
        rowcount = repository.delete(item_id)

    if rowcount > 0:
        return {
            'success': True
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item with ID {item_id} not found.')


@router.post('/proxy_post/{uuid}', name='Proxy POST request', tags=['Proxy'],
             dependencies=[Depends(check_authentication_header)])
async def proxy_post_action(uuid: str, request: Request) -> Union[DataResponseSuccess, dict]:

    with session_maker() as session:
        repository = ProxyRepository(session)
        proxy_item = repository.find_one_by_uuid(uuid)

    if proxy_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item with UUID {uuid} not found.')

    payload = None
    try:
        payload = await request.json()
    except Exception as e:
        print(str(e))

    files = []
    req_headers = dict(request.headers)
    query_params = dict(request.query_params)
    request_url = proxy_item.url

    headers = {
        'Content-Type': req_headers['content-type'] if 'content-type' in req_headers else 'application/json'
    }
    if 'authorization' in req_headers:
        headers['Authorization'] = req_headers['authorization']

    response = requests.request('post', request_url, json=payload, headers=headers, params=query_params, verify=True)

    status_code = int(response.status_code)
    try:
        resp_content = response.content.decode('utf-8')
    except Exception as e:
        print(str(e))
        resp_content = 'Error.'

    if resp_content.startswith('{'):
        resp_content = json.loads(resp_content)

    resp_content_type = response.headers['Content-Type'] if 'Content-Type' in response.headers else None
    resp_content_length = response.headers['Content-Length'] if 'Content-Length' in response.headers else None
    resp_headers = dict(response.headers)
    if 'Content-Length' in resp_headers:
        del resp_headers['Content-Length']

    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=resp_content, headers=resp_headers)

    return resp_content if type(resp_content) is dict else {'result': resp_content}
