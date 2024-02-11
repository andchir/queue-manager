from pydantic import BaseModel

from schemas.task import TaskSchema


class DataResponseSuccess(BaseModel):
    success: bool

    class Config:
        json_schema_extra = {
            'example': {
                'success': True
            }
        }


class DataResponseResult(BaseModel):
    success: bool
    result: str

    class Config:
        json_schema_extra = {
            'example': {
                'success': False,
                'result': 'Result string...'
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
