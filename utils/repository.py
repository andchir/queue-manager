from abc import ABC, abstractmethod
from sqlalchemy import insert, select, update
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
        try:
            stmt = insert(self.model).values(**data).returning(self.model.id)
            res = self.session.execute(stmt).scalar_one()
            self.session.commit()
        except:
            self.session.rollback()
            raise
        return res

    def find_all(self):
        stmt = select(self.model)
        res = self.session.execute(stmt)
        res = [row[0].to_read_model() for row in res.all()]
        return res
