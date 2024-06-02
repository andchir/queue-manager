from pydantic import BaseModel
from schemas.queue_schema import QueueSchema


class TaskSchema(BaseModel):
    id: int
    uuid: str
    name: str
    title: str
    owner: str | None = None
    data: str | None = None
    webhook_url: str | None = None

    class Config:
        from_attributes = True


class TaskDetailedSchema(BaseModel):
    id: int
    uuid: str
    name: str
    title: str
    owner: str | None = None
    data: str | None = None
    webhook_url: str | None = None
    queue: list[QueueSchema] = []

    class Config:
        from_attributes = True


class TaskAddSchema(BaseModel):
    name: str
    title: str
    owner: str | None = None
    data: str | None = None
    webhook_url: str | None = None


class TaskUpdateSchema(BaseModel):
    name: str | None = None
    title: str | None = None
    owner: str | None = None
    data: str | None = None
    webhook_url: str | None = None

    class Config:
        from_attributes = True
