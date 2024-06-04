from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from db.db import Base
from models.queue import generate_uuid
from schemas.proxy_schema import ProxySchema


class Proxy(Base):
    __tablename__ = 'proxy'
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(37), default=generate_uuid)
    url: Mapped[str] = mapped_column(String(256), nullable=True, default=None)
    owner: Mapped[str] = mapped_column(String(256), nullable=True, default=None)

    def to_read_model(self) -> ProxySchema:
        return ProxySchema(
            id=self.id,
            uuid=self.uuid,
            url=self.url,
            owner=self.owner
        )
