from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# =====================================================
# 🔹 BASE
# =====================================================

class StockErrorsBase(BaseModel):
    serial: str
    status:  Optional[str] = None
    message_error: str
    location_id: Optional[int] = None
    error_origin: str
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


# =====================================================
# 🔹 CREATE
# =====================================================

class StockErrorsCreate(StockErrorsBase):
    pass


# =====================================================
# 🔹 UPDATE
# =====================================================

class StockErrorsUpdate(BaseModel):
    serial: Optional[str] = None
    status: Optional[str] = None
    message_error: Optional[str] = None
    location_id: Optional[int] = None
    error_origin: Optional[str] = None
    resolved: Optional[bool] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


# =====================================================
# 🔹 IN DB BASE
# =====================================================

class StockErrorsInDbBase(StockErrorsBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# 🔹 RESPONSE
# =====================================================

class ResponseStockErrors(StockErrorsInDbBase):
    pass
