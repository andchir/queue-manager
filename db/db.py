from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine('sqlite:///app_database.db')
session_maker = sessionmaker(engine)


class Base(DeclarativeBase):
    pass
