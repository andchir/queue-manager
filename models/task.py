from sqlalchemy import ForeignKey
from sqlalchemy import String, UUID
from sqlalchemy.orm import Mapped, mapped_column
from db.db import Base
import uuid

from schemas.task import TaskSchema


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

    def to_read_model(self) -> TaskSchema:
        return TaskSchema(
            id=self.id,
            uuid=self.uuid,
            name=self.name,
            title=self.title,
            owner=self.owner,
            data=self.data
        )
