from sqlalchemy import insert
from models.task import Task
from utils.repository import SQLAlchemyRepository


class TasksRepository(SQLAlchemyRepository):
    model = Task

    def add_one(self, data: dict, item_uuid=None, api_keys=None):
        if item_uuid is not None:
            data['uuid'] = item_uuid
        if api_keys is not None:
            data['api_keys'] = api_keys
        if not self.session.in_transaction():
            self.session.begin()
        stmt = insert(self.model).values(**data)
        try:
            lastrowid = self.session.execute(stmt).lastrowid
        except:
            self.session.rollback()
            raise
        else:
            self.session.commit()
        return self.session.query(self.model).filter_by(id=lastrowid).one().to_read_model()
