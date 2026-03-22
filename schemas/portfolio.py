from typing import Optional

from pydantic import BaseModel


class PortfolioStockCreate(BaseModel):
    code: str
    name: str
    cost_price: float
    shares: int


class PortfolioStockUpdate(BaseModel):
    name: Optional[str] = None
    cost_price: Optional[float] = None
    shares: Optional[int] = None
