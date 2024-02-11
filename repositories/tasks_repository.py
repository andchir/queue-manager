from models.task import Task
from utils.repository import SQLAlchemyRepository


class TasksRepository(SQLAlchemyRepository):
    model = Task
