from typing import Union

from fastapi import APIRouter, Depends, HTTPException, status
from db.db import session_maker
from repositories.tasks_repository import TasksRepository
from schemas.response import DataResponseSuccess
from schemas.task import TaskAddSchema
from utils.security import check_authentication_header

router = APIRouter()


@router.get('/')
def read_root():
    return {'Hello': 'World'}


@router.post('/tasks', name='Create Task', dependencies=[Depends(check_authentication_header)])
def create_task(task: TaskAddSchema):
    with session_maker() as session:
        task_repository = TasksRepository(session)
        task_id = task_repository.add_one(task.model_dump())

    return {
        'success': True,
        'task_id': task_id
    }


@router.get('/tasks', name='Tasks list', dependencies=[Depends(check_authentication_header)])
def create_task():

    with session_maker() as session:
        task_repository = TasksRepository(session)
        res = task_repository.find_all()

    return {
        'success': True,
        'items': res
    }


@router.delete('/tasks/{item_id}', name='Delete task', dependencies=[Depends(check_authentication_header)])
def delete_index_action(item_id: int) -> Union[DataResponseSuccess, dict]:

    with session_maker() as session:
        task_repository = TasksRepository(session)
        rowcount = task_repository.delete(item_id)

    if rowcount > 0:
        return {
            'success': True
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Item with ID {item_id} not found.')

