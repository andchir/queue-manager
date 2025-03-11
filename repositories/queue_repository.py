from sqlalchemy.exc import NoResultFound
from sqlalchemy import select, func
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

    def get_count_by_task_id(self, status_list, task_id):
        try:
            stmt = (select(func.count())
                    .where(
                self.model.task_id == task_id,
                            self.model.status.in_(status_list)
                    )
                    .order_by(self.model.id))
            result = self.session.execute(stmt).scalar()
        except NoResultFound:
            return None
        return result

    def find_by_uuid_and_status(self, uuid, status_list):
        try:
            obj = self.session.query(self.model).filter(Queue.status.in_(status_list)).filter_by(uuid=uuid).one()
        except NoResultFound:
            return None
        return obj

    def find_one_next(self, task_id: int):
        try:
            stmt = (select(self.model)
                    .where(self.model.task_id == task_id, self.model.status == 'pending')
                    .order_by(self.model.id))
            result = self.session.execute(stmt)
        except NoResultFound:
            return None
        return result.first()

    def delete_old(self, limit=10, task_id=None) -> int:
        stmt = (select(self.model).filter_by(task_id=task_id).order_by(self.model.id.asc()).limit(limit)
                if task_id is not None
                else select(self.model).order_by(self.model.id.asc()).limit(limit))

        rowcount = 0

        try:
            res = self.session.execute(stmt)
            for item in res.all():
                self.session.delete(item[0])
                rowcount += 1
        except:
            self.session.rollback()
            raise
        else:
            self.session.commit()

        return rowcount
