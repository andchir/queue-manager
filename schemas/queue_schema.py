from pydantic import BaseModel
from datetime import datetime


class QueueSchema(BaseModel):
    id: int
    task_id: int
    uuid: str
    status: str
    owner: str | None = None
    data: dict | None = None
    result_data: dict | None = None
    headers: dict | None = None
    time_created: str | datetime | None = None
    time_updated: str | datetime | None = None
    user_id: int | None = None
    number: int = 0
    pending: int = 0

    class Config:
        from_attributes = True


class QueueDetailedSchema(BaseModel):
    id: int
    task_id: int
    uuid: str
    status: str
    owner: str | None = None
    data: dict | None = None
    result_data: dict | None = None
    headers: dict | None = None
    user_id: int | None = None

    class Config:
        from_attributes = True


class QueueAddSchema(BaseModel):
    status: str
    task_id: int | None = None
    owner: str | None = None
    data: dict | None = None
    result_data: dict | None = None
    headers: dict | None = None
    user_id: int | None = None

    class Config:
        from_attributes = True


class QueueUpdateSchema(BaseModel):
    owner: str | None = None
    data: dict | None = None

    class Config:
        from_attributes = True


class QueueResultSchema(BaseModel):
    result_data: dict | None = None

    class Config:
        from_attributes = True


class QueueSizeSchema(BaseModel):
    queue_size: int = 0

    class Config:
        from_attributes = True

