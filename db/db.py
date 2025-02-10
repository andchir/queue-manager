from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import settings

if settings.sqlite_db_name:
    engine = create_engine('sqlite:///' + settings.sqlite_db_name)
else:
    engine = create_engine(
        'mysql+pymysql://' + settings.mysql_connection_string,
        # 'mariadb+pymysql://' + settings.mysql_connection_string
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=True,
    )
session_maker = sessionmaker(engine)


class Base(DeclarativeBase):
    pass
