from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'Queue Manager'
    admin_email: str = 'aaa@bbb.cc'
    api_keys: str = ''

    class Config:
        env_file = '.env'


settings = Settings()
