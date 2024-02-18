from models.queue import Queue
from utils.repository import SQLAlchemyRepository


class QueueRepository(SQLAlchemyRepository):
    model = Queue
