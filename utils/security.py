from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from starlette import status
from config import settings

api_key_header = APIKeyHeader(name='API-KEY')


def check_authentication_header(api_key: str = Depends(api_key_header)):
    api_keys = settings.api_keys.split(',')
    if api_key in api_keys:
        return {}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid API Key.',
    )
