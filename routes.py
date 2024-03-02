from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound

from db.db import session_maker
from repositories.queue_repository import QueueRepository
from repositories.tasks_repository import TasksRepository
from schemas.queue_schema import QueueAddSchema, QueueUpdateSchema
from schemas.response import DataResponseSuccess, ResponseTasksItems, ResponseItemId, ResponseQueueItems
from schemas.task_schema import TaskAddSchema, TaskUpdateSchema, TaskSchema, TaskDetailedSchema
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
        task_id = task_repository.add_one(task.model_dump())

    return {
        'success': True,
        'task_id': task_id
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
def create_queue_action(queue_item: QueueUpdateSchema, task_id: int) -> Union[ResponseItemId, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        task = task_repository.find_one(task_id)
    if task is not None:
        queue_item_new = QueueAddSchema(status='pending', task_id=task.id, **queue_item.model_dump())
        with session_maker() as session:
            queue_repository = QueueRepository(session)
            queue_item_id = queue_repository.add_one(queue_item_new.model_dump())
        return {
            'success': True,
            'queue_item_id': queue_item_id
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
