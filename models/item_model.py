import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base


class Item(Base):
    __tablename__ = "logistic_stock_item"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    product_id = Column(Integer, ForeignKey(
        "logistic_stock_product.id"), nullable=True, index=True)

    serial = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, nullable=False, index=True)
    location_id = Column(Integer, ForeignKey(
        "logistica_groupaditionalinformation.id"), nullable=False, index=True)
    extra_info = Column(JSON)
    product = relationship("Product")
    location = relationship("Location")
