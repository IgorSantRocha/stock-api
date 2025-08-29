from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from models.movement_model import MovementType


class MovementBase(BaseModel):
    movement_type: MovementType
    item_id: int
    product_id: int

    from_location_id: Optional[int] = None
    to_location_id: Optional[int] = None

    order_origin: Optional[str] = None       # ex.: "CIELO", "INTELIPOST"
    order_number: Optional[str] = None
    volume_number: Optional[int] = Field(default=None, ge=0)
    kit_number: Optional[str] = None

    extra_info: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None

    # Pydantic v2
    model_config = {"from_attributes": True, "use_enum_values": True}
    # v1:
    # class Config:
    #     orm_mode = True
    #     use_enum_values = True


class MovementCreate(MovementBase):
    pass


class MovementUpdate(MovementBase):
    pass  # se quiser PATCH estrito, torne todos os campos opcionais aqui


class MovementInDbBase(MovementBase):
    id: int
    created_at: datetime


class Movement(MovementInDbBase):
    pass
