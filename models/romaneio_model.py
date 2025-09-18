import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base


class Romaneio(Base):
    __tablename__ = "logistic_stock_reverse_item"
    id = Column(Integer, primary_key=True)

    item_id = Column(Integer, ForeignKey(
        "logistic_stock_item.id"), nullable=True, index=True)
    volume_number = Column(String, nullable=False)
    kit_number = Column(String, nullable=True)

    status_rom = Column(String, nullable=False, default="ABERTO", index=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_by = Column(String, nullable=False)
    update_at = Column(DateTime, onupdate=func.now())
    update_by = Column(String, nullable=True)

    item = relationship("Item", foreign_keys=[item_id])

    # define reverse_item_name como AR0000id
    @property
    def reverse_item_name(self):
        return f"AR{str(self.id).zfill(5)}"
