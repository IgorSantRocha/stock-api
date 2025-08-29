import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base


class MovementType(enum.Enum):
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    ADJUST = "ADJUST"
    RETURN = "RETURN"
    PICK = "PICK"
    PACK = "PACK"


class Movement(Base):
    __tablename__ = "logistic_stock_movement"
    id = Column(Integer, primary_key=True)
    movement_type = Column(Enum(MovementType), nullable=False, index=True)

    item_id = Column(Integer, ForeignKey("logistic_stock_item.id"),
                     nullable=False, index=True)
    product_id = Column(Integer, ForeignKey(
        "logistic_stock_product.id"), nullable=False, index=True)

    from_location_id = Column(Integer, ForeignKey(
        "logistica_groupaditionalinformation.id"))
    to_location_id = Column(Integer, ForeignKey(
        "logistica_groupaditionalinformation.id"))

    order_origin = Column(String, index=True)   # ex.: "CIELO", "INTELIPOST"
    order_number = Column(String, index=True)
    volume_number = Column(Integer)
    kit_number = Column(String, index=True)

    extra_info = Column(JSON)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_by = Column(String)

    item = relationship("Item")
    product = relationship("Product")
