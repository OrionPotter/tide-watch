from pydantic import BaseModel


class Position(BaseModel):
    price: float
    shares: int


class CalculateCostRequest(BaseModel):
    positions: list[Position]


class ExportKlineRequest(BaseModel):
    code: str
    format: str = 'csv'
    start_date: str = None
    end_date: str = None
