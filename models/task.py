from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.db import Base
import uuid

from schemas.task_schema import TaskSchema


def generate_uuid():
    return str(uuid.uuid4())


class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(128), default=generate_uuid)
    name: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(256))
    owner: Mapped[str] = mapped_column(String(256), default=None)
    data: Mapped[str] = mapped_column(String(256), default=None)

    queue: Mapped[List['Queue']] = relationship(back_populates='task', cascade='all, delete-orphan')

    def to_read_model(self) -> TaskSchema:
        return TaskSchema(
            id=self.id,
            uuid=self.uuid,
            name=self.name,
            title=self.title,
            owner=self.owner,
            data=self.data
        )
