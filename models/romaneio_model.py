import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base


class Romaneio(Base):
    __tablename__ = "logistic_stock_reverse"
    id = Column(Integer, primary_key=True)

    status_rom = Column(String, nullable=False, default="ABERTO", index=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_by = Column(String, nullable=False)
    update_at = Column(DateTime, onupdate=func.now())
    update_by = Column(String, nullable=True)

    # define reverse_item_name como AR0000id
    @property
    def reverse_item_name(self):
        return f"AR{str(self.id).zfill(5)}"
