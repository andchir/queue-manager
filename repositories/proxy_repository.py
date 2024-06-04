from utils.repository import SQLAlchemyRepository
from models.proxy import Proxy


class ProxyRepository(SQLAlchemyRepository):
    model = Proxy
