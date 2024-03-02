from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import settings

engine = create_engine('sqlite:///' + settings.sqlite_db_name)
session_maker = sessionmaker(engine)


class Base(DeclarativeBase):
    pass
