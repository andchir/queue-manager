from pydantic import BaseModel

from schemas.proxy_schema import ProxySchema
from schemas.queue_schema import QueueSchema
from schemas.task_schema import TaskSchema


class DataResponseSuccess(BaseModel):
    success: bool

    class Config:
        json_schema_extra = {
            'example': {
                'success': True
            }
        }


class DataResponseMessage(BaseModel):
    success: bool
    msg: str

    class Config:
        json_schema_extra = {
            'example': {
                'success': False,
                'msg': 'Item not found.'
            }
        }


class ResponseTasksItems(BaseModel):
    items: list[TaskSchema]

    class Config:
        from_attributes = True


class ResponseItemId(BaseModel):
    success: bool
    item_id: int
    item_uuid: str

    class Config:
        from_attributes = True


class ResponseItemUuid(BaseModel):
    success: bool
    uuid: str
    url: str

    class Config:
        from_attributes = True


class ResponseQueueItems(BaseModel):
    items: list[QueueSchema]

    class Config:
        from_attributes = True


class ResponseProxyItems(BaseModel):
    items: list[ProxySchema]

    class Config:
        from_attributes = True
