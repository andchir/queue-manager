from fastapi import APIRouter

from db.db import session_maker
from repositories.tasks import TasksRepository
from schemas.task import TaskAddSchema

router = APIRouter()


@router.get('/')
def read_root():
    return {'Hello': 'World'}


@router.post('/tasks', name='Create Task')
def create_task(task: TaskAddSchema):
    with session_maker() as session:
        task_repository = TasksRepository(session)
        tasks_dict = task.model_dump()
        res = task_repository.add_one(tasks_dict)
        task_id = res

    return {
        'success': True,
        'task_id': task_id
    }


@router.get('/tasks', name='Tasks list')
def create_task():

    with session_maker() as session:
        task_repository = TasksRepository(session)
        res = task_repository.find_all()

    return {
        'success': True,
        'items': res
    }
