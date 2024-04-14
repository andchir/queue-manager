import datetime
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Request, status
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

router = APIRouter()


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
        'task_id': task.id
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
def get_tasks_action(task_id: int) -> Union[TaskDetailedSchema, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        res = task_repository.find_one(task_id)

    if res is not None:
        return res
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Task with ID {task_id} not found.')


@router.get('/tasks', name='Tasks list', tags=['Tasks'],
            dependencies=[Depends(check_authentication_header)],
            response_model=ResponseTasksItems)
def get_tasks_action() -> Union[ResponseTasksItems, dict]:
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


@router.post('/queue/{task_id}', name='Create Queue Item', tags=['Queue'],
             dependencies=[Depends(check_authentication_header)])
def create_queue_action(queue_item: QueueUpdateSchema, task_id: int, request: Request) -> Union[ResponseItemUuid, dict]:

    restore_outdated_queue_items()

    with session_maker() as session:
        task_repository = TasksRepository(session)
        task = task_repository.find_one(task_id)
    if task is not None:
        queue_item_new = QueueAddSchema(status=QueueStatus.PENDING.value, task_id=task.id, **queue_item.model_dump())
        with session_maker() as session:
            queue_repository = QueueRepository(session)
            queue_item = queue_repository.add_one(queue_item_new.model_dump())
        base_url = f'{request.url.scheme}://{request.client.host}'
        if request.url.port != 80:
            base_url += f':{request.url.port}'
        return {
            'success': True if queue_item is not None else False,
            'uuid': queue_item.uuid if queue_item is not None else None,
            'url': f'{base_url}/queue/{queue_item.uuid}'
            if queue_item is not None else None
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Task with ID {task_id} not found.')


@router.get('/queue', name='Queue list', tags=['Queue'],
            dependencies=[Depends(check_authentication_header)],
            response_model=ResponseQueueItems)
def get_queue_action() -> Union[ResponseQueueItems, dict]:
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
        res = queue_repository.find_one_by_uuid(uuid)
    if res is not None:
        return res.to_read_model()
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item with UUID "{uuid}" not found.')


@router.get('/queue_next/{task_id}', name='Get Next Queue Item', tags=['Queue'],
            dependencies=[Depends(check_authentication_header)])
def get_queue_action(task_id: int) -> Union[QueueSchema, dict]:

    restore_outdated_queue_items()

    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_one_next(task_id)
    if res is not None:
        queue_item = res[0]
        result = queue_repository.update_one({
            'status': QueueStatus.PROCESSING.value,
            'time_updated': datetime.datetime.utcnow()
        }, queue_item.id)
        return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item not found.')


@router.post('/queue_result/{uuid}', name='Send Queue Item result', tags=['Queue'])
def get_queue_action(queue_item: QueueResultSchema, uuid: str) -> Union[QueueSchema, dict]:

    restore_outdated_queue_items()

    with session_maker() as session:
        queue_repository = QueueRepository(session)
        res = queue_repository.find_one_by_uuid(uuid)
    if hasattr(queue_item, 'result_data') and res is not None and res.status == QueueStatus.PROCESSING.value:
        result = queue_repository.update_one({
            'status': QueueStatus.COMPLETED.value,
            'result_data': queue_item.result_data,
            'time_updated': datetime.datetime.utcnow()
        }, res.id)
        return result
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Queue item not found.')
