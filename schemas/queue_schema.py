from pydantic import BaseModel


class QueueSchema(BaseModel):
    id: int
    task_id: int
    uuid: str
    status: str
    owner: str | None = None
    data: dict | None = None
    result_data: dict | None = None
    time_created: str | None = None
    time_updated: str | None = None
    number: int = 0

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

    class Config:
        from_attributes = True


class QueueAddSchema(BaseModel):
    status: str
    task_id: int | None = None
    owner: str | None = None
    data: dict | None = None
    result_data: dict | None = None

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
