from typing import Optional
from pydantic import BaseModel


class OrderOriginBase(BaseModel):
    origin_name: str
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    model_config = {"from_attributes": True}


class OrderOriginCreate(OrderOriginBase):
    pass


class OrderOriginUpdate(OrderOriginBase):
    pass


class OrderOriginInDbBase(OrderOriginBase):
    id: int


class OrderOrigin(OrderOriginInDbBase):
    pass
