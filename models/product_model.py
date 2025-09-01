import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base


class Product(Base):
    __tablename__ = "logistic_stock_product"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    sku = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=False, index=True)
    category = Column(String, index=True)
    client_name = Column(String, index=True)
    created_by = Column(String),
    extra_info = Column(JSON)
