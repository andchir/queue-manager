from typing import Optional
from pydantic import BaseModel


class TaskSchema(BaseModel):
    id: int
    uuid: str
    name: str
    title: str
    owner: str = None
    data: str = None

    class Config:
        from_attributes = True


class TaskAddSchema(BaseModel):
    name: str
    title: str
    owner: str = None
    data: str = None
