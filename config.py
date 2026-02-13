from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'Queue Manager'
    app_server_name: str = 'queue.api2app.ru'
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
    bothub_api_key: str = ''
    vsegpt_api_key: str = ''
    use_task_api_keys: bool = False
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 10

    class Config:
        env_file = '.env'


settings = Settings()
