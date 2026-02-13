import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone


class Client(Base):
    __tablename__ = "logistic_stock_client"
    id = Column(Integer, primary_key=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),  # ✅ Python
        server_default=func.now(),
        nullable=False
    )
    client_code = Column(String, unique=True, index=True, nullable=False)
    client_name = Column(String, index=True)
    created_by = Column(String)
    extra_info = Column(JSON)
