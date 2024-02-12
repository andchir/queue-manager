from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.db import Base
import uuid
import datetime


def generate_uuid():
    return str(uuid.uuid4())


class Queue(Base):
    __tablename__ = 'queue'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(37), default=generate_uuid)
    status: Mapped[str] = mapped_column(String(30))
    data: Mapped[str] = mapped_column(String(256), default=None)
    owner: Mapped[str] = mapped_column(String(256), default=None)
    time_created: Mapped[str] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    time_updated: Mapped[str] = mapped_column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id'))
    task: Mapped['Task'] = relationship(back_populates='queue')

