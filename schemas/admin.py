from pydantic import BaseModel


class AdminStockCreate(BaseModel):
    code: str
    name: str
    cost_price: float
    shares: int


class AdminStockUpdate(BaseModel):
    name: str
    cost_price: float
    shares: int


class AdminMonitorStockCreate(BaseModel):
    code: str
    name: str
    timeframe: str
    reasonable_pe_min: float = 15
    reasonable_pe_max: float = 20


class AdminMonitorStockUpdate(BaseModel):
    name: str
    timeframe: str
    reasonable_pe_min: float = 15
    reasonable_pe_max: float = 20


class ToggleEnabled(BaseModel):
    enabled: bool = True


class XueqiuCubeCreate(BaseModel):
    cube_symbol: str
    cube_name: str
    enabled: bool = True


class XueqiuCubeUpdate(BaseModel):
    cube_name: str
    enabled: bool = True
