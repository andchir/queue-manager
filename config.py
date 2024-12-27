from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'Queue Manager'
    admin_email: str = 'aaa@bbb.cc'
    api_keys: str = ''
    sqlite_db_name: str = 'app_database.db'
    max_execution_time: int = 14400
    max_store_time: int = 43200
    gdrive_folder_id: str = ''
    yadisk_token: str = ''
    ws_enabled: str = 'true'
    tg_bot_token: str = ''
    tg_chat_id: str = ''

    class Config:
        env_file = '.env'


settings = Settings()
