from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import settings

if settings.sqlite_db_name:
    engine = create_engine('sqlite:///' + settings.sqlite_db_name)
else:
    engine = create_engine(
        'mysql+pymysql://' + settings.mysql_connection_string
    )
session_maker = sessionmaker(engine)


class Base(DeclarativeBase):
    pass
