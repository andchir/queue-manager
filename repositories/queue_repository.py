from sqlalchemy.exc import NoResultFound
from sqlalchemy import select
from models.queue import Queue
from utils.repository import SQLAlchemyRepository

from models.queue import Queue
from models.task import Task


class QueueRepository(SQLAlchemyRepository):
    model = Queue

    def find_one_next(self):
        try:
            stmt = select(self.model).where(self.model.status == 'pending').order_by(self.model.id)
            result = self.session.execute(stmt)
        except NoResultFound:
            return None
        return result.first()
