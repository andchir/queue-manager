from sqlalchemy.exc import NoResultFound
from sqlalchemy import select
from models.queue import Queue
from utils.repository import SQLAlchemyRepository

from models.queue import Queue
from models.task import Task


class QueueRepository(SQLAlchemyRepository):
    model = Queue

    def find_by_status(self, status, task_id=None):
        try:
            stmt = (select(self.model)
                    .where(*((self.model.status == status,) if task_id is None else (self.model.task_id == task_id, self.model.status == status)))
                    .order_by(self.model.id))
            result = self.session.execute(stmt)
        except NoResultFound:
            return None
        return result

    def find_one_next(self, task_id: int):
        try:
            stmt = (select(self.model)
                    .where(self.model.task_id == task_id, self.model.status == 'pending')
                    .order_by(self.model.id))
            result = self.session.execute(stmt)
        except NoResultFound:
            return None
        return result.first()
