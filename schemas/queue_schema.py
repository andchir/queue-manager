from typing import Optional
from pydantic import BaseModel

from schemas.task_schema import TaskSchema


class QueueSchema(BaseModel):
    id: int
    task_id: int
    uuid: str
    status: str
    owner: str | None = None
    data: str | None = None

    class Config:
        from_attributes = True


class QueueAddSchema(BaseModel):
    status: str
    task_id: int | None = None
    owner: str | None = None
    data: str | None = None


class QueueUpdateSchema(BaseModel):
    status: str | None = None
    owner: str | None = None
    data: str | None = None

    class Config:
        from_attributes = True
