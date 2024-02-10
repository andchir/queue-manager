from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'Queue Manager'
    admin_email: str = 'aaa@bbb.cc'

    class Config:
        env_file = '.env'


settings = Settings()
