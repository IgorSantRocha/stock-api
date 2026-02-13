from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Boolean, Column, Integer, String, DateTime, ForeignKey, JSON, Enum, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from db.base_class import Base
from sqlalchemy.orm import declarative_base
from sqlalchemy import Index, text


class StockErrors(Base):
    __tablename__ = "logistic_stock_errors"

    id = Column(Integer, primary_key=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),  # ✅ Python
        server_default=func.now(),
        nullable=False
    )
    serial = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, nullable=False, index=True)

    message_error = Column(String, nullable=False)

    location_id = Column(Integer, ForeignKey(
        "logistica_groupaditionalinformation.id"), nullable=False, index=True)

    error_origin = Column(String, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
