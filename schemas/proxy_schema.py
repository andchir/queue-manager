from pydantic import BaseModel


class ProxySchema(BaseModel):
    id: int
    uuid: str
    url: str
    owner: str | None

    class Config:
        from_attributes = True


class ProxyAddSchema(BaseModel):
    url: str
    owner: str | None = None
