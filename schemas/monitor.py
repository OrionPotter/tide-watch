from typing import Optional

from pydantic import BaseModel


class MonitorStockCreate(BaseModel):
    code: str
    name: str
    timeframe: str
    reasonable_pe_min: float = 15
    reasonable_pe_max: float = 20


class MonitorStockUpdate(BaseModel):
    name: Optional[str] = None
    timeframe: Optional[str] = None
    reasonable_pe_min: Optional[float] = None
    reasonable_pe_max: Optional[float] = None


class ToggleStock(BaseModel):
    enabled: bool = True


class UpdateKline(BaseModel):
    force_update: bool = False
