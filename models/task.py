from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.db import Base
import uuid

from schemas.task_schema import TaskDetailedSchema


def generate_uuid():
    return str(uuid.uuid4())


class Task(Base):
    __tablename__ = 'tasks'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(128), default=generate_uuid)
    name: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(256))
    owner: Mapped[str] = mapped_column(String(256), nullable=True, default=None)
    data: Mapped[str] = mapped_column(String(512), nullable=True, default=None)
    webhook_url: Mapped[str] = mapped_column(String(256), nullable=True, default=None)
    api_keys: Mapped[str] = mapped_column(String(256), nullable=True, default=None)

    queue_list = relationship('models.queue.Queue', back_populates='task', cascade='all,delete-orphan',
                              single_parent=True, lazy='subquery', passive_deletes=True)

    def to_read_model(self) -> TaskDetailedSchema:
        return TaskDetailedSchema(
            id=self.id,
            uuid=self.uuid,
            name=self.name,
            title=self.title,
            owner=self.owner,
            data=self.data,
            webhook_url=self.webhook_url,
            api_keys=self.api_keys,
            queue_list=self.queue_list
        )
