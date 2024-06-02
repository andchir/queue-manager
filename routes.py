import datetime
import json
import os
from typing import Union, Any

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status, UploadFile, Form, Body
from sqlalchemy.exc import NoResultFound

from db.db import session_maker
from models.queue import QueueStatus
from repositories.queue_repository import QueueRepository
from repositories.tasks_repository import TasksRepository
from schemas.queue_schema import QueueAddSchema, QueueUpdateSchema, QueueSchema, QueueResultSchema
from schemas.response import DataResponseSuccess, ResponseTasksItems, ResponseItemId, ResponseQueueItems, \
    ResponseItemUuid
from schemas.task_schema import TaskAddSchema, TaskUpdateSchema, TaskSchema, TaskDetailedSchema
from utils.restore_outdated_queue_items import restore_outdated_queue_items
from utils.security import check_authentication_header
from utils.upload_file import upload_file, delete_old_files

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
        video_file: UploadFile = None,
        audio_file: UploadFile = None
) -> Union[ResponseItemUuid, dict]:

    data = json.loads(data) if data else {}
    if 'data' not in data:
        data['data'] = data.copy()
        if 'owner' in data:
            del data['owner']
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

    if video_file is not None:
        file_name = upload_file(video_file, upload_dir_path, type='video')
        if file_name:
            data['data']['video_file'] = f'{base_url}/uploads/{file_name}'

    if audio_file is not None:
        file_name = upload_file(audio_file, upload_dir_path, type='audio')
        if file_name:
            data['data']['audio_file'] = f'{base_url}/uploads/{file_name}'

    with session_maker() as session:
        task_repository = TasksRepository(session)
        task = task_repository.find_one_by_uuid(task_uuid)

    if task is not None:
        queue_item_new = QueueAddSchema(status=QueueStatus.PENDING.value, task_id=task.id, **data)
        with session_maker() as session:
            queue_repository = QueueRepository(session)
            queue_item = queue_repository.add_one(queue_item_new.model_dump())
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
def get_queue_list_action() -> Union[ResponseQueueItems, dict]:
    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_all()

    return {
        'items': res
    }


@router.get('/queue/{uuid}', name='Get Queue Item State', tags=['Queue'],
            dependencies=[Depends(check_authentication_header)])
def get_queue_action(uuid: str) -> Union[QueueSchema, dict]:
    with session_maker() as session:
        queue_repository = QueueRepository(session)
        queue_item = queue_repository.find_one_by_uuid(uuid)
    if queue_item is not None:
        with session_maker() as session:
            queue_repository = QueueRepository(session)
            queue_list = queue_repository.find_by_status(QueueStatus.PENDING.value, task_id=queue_item.task_id)
            queue_index = next((index for (index, d) in enumerate(list(queue_list)) if d[0].uuid == uuid), None)
        result = queue_item.to_read_model()
        result.number = queue_index + 1 if queue_index is not None else 0
        return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item with UUID "{uuid}" not found.')


@router.get('/queue_next/{task_uuid}', name='Get Next Queue Item', tags=['Queue'])
def get_queue_next_action(task_uuid: str, user_ip: str = Header(None, alias='X-Real-IP')) -> Union[QueueSchema, dict]:

    restore_outdated_queue_items()

    with session_maker() as session:
        task_repository = TasksRepository(session)
        task = task_repository.find_one_by_uuid(task_uuid)

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Task not found.')

    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_one_next(task.id)
    if res is not None:
        queue_item = res[0]
        result = queue_repository.update_one({
            'owner': user_ip if user_ip is not None else '',
            'status': QueueStatus.PROCESSING.value,
            'time_updated': datetime.datetime.utcnow()
        }, queue_item.id)
        return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item not found.')


@router.post('/queue_result/{uuid}', name='Send Queue Item result', tags=['Queue'])
def set_queue_result_action(queue_item: QueueResultSchema, uuid: str) -> Union[QueueSchema, dict]:

    restore_outdated_queue_items()

    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_by_uuid_and_status(uuid, QueueStatus.PROCESSING.value)
    if hasattr(queue_item, 'result_data') and res is not None:
        result = queue_repository.update_one({
            'status': QueueStatus.COMPLETED.value,
            'result_data': queue_item.result_data,
            'time_updated': datetime.datetime.utcnow()
        }, res.id)
        return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item not found.')


@router.post('/queue_error/{uuid}', name='Send Queue Item error', tags=['Queue'])
def set_queue_result_action(uuid: str, message: str = Form()) -> Union[QueueSchema, dict]:
    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_by_uuid_and_status(uuid, QueueStatus.PROCESSING.value)
    if res is not None:
        result = queue_repository.update_one({
            'status': QueueStatus.ERROR.value,
            'result_data': {'message': message},
            'time_updated': datetime.datetime.utcnow()
        }, res.id)
        return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item not found.')
