from abc import ABC, abstractmethod
from sqlalchemy import insert, select, update, delete
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound


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

    def add_one(self, data: dict, item_uuid=None):
        if item_uuid is not None:
            data['uuid'] = item_uuid
        if not self.session.in_transaction():
            self.session.begin()
        stmt = insert(self.model).values(**data)# .returning(self.model)
        try:
            lastrowid = self.session.execute(stmt).inserted_primary_key[0]#.lastrowid# .scalar_one()
        except:
            self.session.rollback()
            raise
        else:
            self.session.commit()
        return self.session.query(self.model).filter_by(id=lastrowid).one().to_read_model()
        # return res.to_read_model() if res else None

    def update_one(self, data: dict, item_id: int):
        if not self.session.in_transaction():
            self.session.begin()
        stmt = update(self.model).where(self.model.id == item_id).values(**data)# .returning(self.model)
        try:
            lastrowid = self.session.execute(stmt).inserted_primary_key[0]# .lastrowid# .scalar()
        except:
            self.session.rollback()
            raise
        else:
            self.session.commit()
        return self.session.query(self.model).filter_by(id=lastrowid).one().to_read_model()

    def find_one(self, item_id: int):
        try:
            obj = self.session.get_one(self.model, item_id)
        except NoResultFound:
            return None
        return obj

    def find_one_by_uuid(self, uuid: str):
        try:
            obj = self.session.query(self.model).filter_by(uuid=uuid).one()
        except NoResultFound:
            return None
        return obj

    def find_all(self, filter=None, limit=100, sort_dir='desc'):
        sort_dir_opt = self.model.id.desc() if sort_dir == 'desc' else self.model.id.asc()
        stmt = select(self.model).filter_by(**filter).order_by(sort_dir_opt).limit(limit) if filter \
            else select(self.model).order_by(sort_dir_opt).limit(limit)
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
