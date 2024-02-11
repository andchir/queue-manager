from pydantic import BaseModel


class DataResponseSuccess(BaseModel):
    success: bool

    class Config:
        json_schema_extra = {
            'example': {
                'success': True
            }
        }


class DataResponseDetails(BaseModel):
    result: str
    details: str

    class Config:
        json_schema_extra = {
            'example': {
                'success': False,
                'details': 'Item not found.'
            }
        }


class DataResponseResult(BaseModel):
    result: str
    result: str

    class Config:
        json_schema_extra = {
            'example': {
                'success': False,
                'result': 'Result string...'
            }
        }
