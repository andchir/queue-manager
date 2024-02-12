from pydantic import BaseModel

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
    success: bool
    items: list[TaskSchema]

    class Config:
        from_attributes = True


class ResponseItemId(BaseModel):
    success: bool
    item_id: int

    class Config:
        from_attributes = True
