from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound

from db.db import session_maker
from repositories.tasks_repository import TasksRepository
from schemas.response import DataResponseSuccess, ResponseTasksItems, ResponseItemId
from schemas.task_schema import TaskAddSchema, TaskUpdateSchema
from utils.security import check_authentication_header

router = APIRouter()


@router.get('/')
def read_root():
    return {'Hello': 'World'}


@router.post('/tasks', name='Create Task',
             dependencies=[Depends(check_authentication_header)])
def create_task_action(task: TaskAddSchema) -> Union[ResponseItemId, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        task_id = task_repository.add_one(task.model_dump())

    return {
        'success': True,
        'task_id': task_id
    }


@router.patch('/tasks/{item_id}', name='Update Task',
              dependencies=[Depends(check_authentication_header)],
              response_model=DataResponseSuccess)
def update_task_action(task: TaskUpdateSchema, item_id: int) -> Union[DataResponseSuccess, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        try:
            task_repository.update_one(task.model_dump(exclude_unset=True), item_id)
        except NoResultFound:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item with ID {item_id} not found.')

    return {
        'success': True
    }


@router.get('/tasks', name='Tasks list',
            dependencies=[Depends(check_authentication_header)],
            response_model=ResponseTasksItems)
def get_tasks_action() -> Union[ResponseTasksItems, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        res = task_repository.find_all()

    return {
        'success': True,
        'items': res
    }


@router.delete('/tasks/{item_id}', name='Delete task',
               dependencies=[Depends(check_authentication_header)],
               response_model=DataResponseSuccess)
def delete_task_action(item_id: int) -> Union[DataResponseSuccess, dict]:
    with session_maker() as session:
        task_repository = TasksRepository(session)
        rowcount = task_repository.delete(item_id)

    if rowcount > 0:
        return {
            'success': True
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item with ID {item_id} not found.')
