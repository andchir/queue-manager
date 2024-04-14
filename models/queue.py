from enum import Enum

from sqlalchemy import JSON, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.db import Base
import uuid
import datetime

from schemas.queue_schema import QueueSchema


class QueueStatus(Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    CANCELED = 'canceled'
    ERROR = 'error'


def generate_uuid():
    return str(uuid.uuid4())


class Queue(Base):
    __tablename__ = 'queue'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(37), default=generate_uuid)
    status: Mapped[str] = mapped_column(String(30))  # pending, processing, canceled, completed, error
    data: Mapped[dict] = mapped_column(JSON(none_as_null=True), nullable=True, default=None)
    result_data: Mapped[dict] = mapped_column(JSON(none_as_null=True), nullable=True, default=None)
    owner: Mapped[str] = mapped_column(String(256), default=None)
    time_created: Mapped[str] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    time_updated: Mapped[str] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id', ondelete='CASCADE'))
    task = relationship('models.task.Task', back_populates='queue',
                        cascade='all,delete', lazy='subquery', passive_deletes=True)

    def to_read_model(self) -> QueueSchema:
        return QueueSchema(
            id=self.id,
            task_id=self.task_id,
            uuid=self.uuid,
            status=self.status,
            owner=self.owner,
            data=self.data,
            time_created=self.time_created.strftime('%Y-%m-%d %H:%M:%S'),
            time_updated=self.time_updated.strftime('%Y-%m-%d %H:%M:%S')
        )
