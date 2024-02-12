from abc import ABC, abstractmethod
from sqlalchemy import insert, select, update, delete
from sqlalchemy.orm import Session


class AbstractRepository(ABC):
    @abstractmethod
    def add_one(self, data: dict):
        raise NotImplementedError

    @abstractmethod
    def find_all(self):
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository):
    model = None

    def __init__(self, session: Session):
        self.session = session

    def add_one(self, data: dict) -> int:
        self.session.begin()
        stmt = insert(self.model).values(**data).returning(self.model.id)
        try:
            res = self.session.execute(stmt).scalar_one()
        except:
            self.session.rollback()
            raise
        else:
            self.session.commit()
        return res

    def update_one(self, data: dict, item_id: int) -> int:
        self.session.begin()
        stmt = update(self.model).where(self.model.id == item_id).values(**data).returning(self.model.id)
        try:
            res = self.session.execute(stmt).scalar_one()
        except:
            self.session.rollback()
            raise
        else:
            self.session.commit()
        return res

    def find_all(self):
        stmt = select(self.model)
        res = self.session.execute(stmt)
        res = [row[0].to_read_model() for row in res.all()]
        return res

    def delete(self, item_id: int) -> int:
        stmt = delete(self.model).where(self.model.id == item_id)
        try:
            res = self.session.execute(stmt)
        except:
            self.session.rollback()
            raise
        else:
            self.session.commit()
        return res.rowcount
