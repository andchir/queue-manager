from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.db import Base
import uuid
import datetime

from schemas.queue_schema import QueueSchema


def generate_uuid():
    return str(uuid.uuid4())


class Queue(Base):
    __tablename__ = 'queue'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(37), default=generate_uuid)
    status: Mapped[str] = mapped_column(String(30))
    data: Mapped[str] = mapped_column(String(512), default=None)
    owner: Mapped[str] = mapped_column(String(256), default=None)
    time_created: Mapped[str] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    time_updated: Mapped[str] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id'))
    task = relationship('models.task.Task', back_populates='queue', cascade='save-update', lazy='subquery')

    def to_read_model(self) -> QueueSchema:
        return QueueSchema(
            id=self.id,
            task_id=self.task_id,
            uuid=self.uuid,
            status=self.status,
            owner=self.owner,
            data=self.data
        )
