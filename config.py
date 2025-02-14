from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'Queue Manager'
    admin_email: str = 'aaa@bbb.cc'
    api_keys: str = ''
    sqlite_db_name: str = 'app_database.db'
    mysql_connection_string: str = 'user:pass@some_mariadb/dbname?charset=utf8mb4'
    max_execution_time: int = 14400
    max_store_time: int = 43200
    gdrive_folder_id: str = ''
    yadisk_token: str = ''
    ws_enabled: str = 'true'
    ws_port: int = 8765
    tg_bot_token: str = ''
    tg_chat_id: str = ''

    class Config:
        env_file = '.env'


settings = Settings()
