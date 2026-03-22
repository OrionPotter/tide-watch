from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from repositories.portfolio_repository import StockRepository
from services.portfolio_service import PortfolioService
from utils.api_helpers import current_timestamp, status_message_response, success_response
from utils.logger import get_logger

logger = get_logger('portfolio_routes')

portfolio_router = APIRouter()


class StockCreate(BaseModel):
    code: str
    name: str
    cost_price: float
    shares: int


class StockUpdate(BaseModel):
    name: Optional[str] = None
    cost_price: Optional[float] = None
    shares: Optional[int] = None


@portfolio_router.get('')
async def get_portfolio():
    logger.info('GET /api/portfolio')
    try:
        rows, summary = await PortfolioService.get_portfolio_data()
        return success_response(
            timestamp=current_timestamp(),
            rows=rows,
            summary=summary,
            clean_nan=True,
        )
    except Exception as exc:
        logger.error(f'GET /api/portfolio failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))


@portfolio_router.post('')
async def create_stock(data: StockCreate):
    logger.info(f'POST /api/portfolio {data.code}')
    success, msg = await StockRepository.add(data.code, data.name, data.cost_price, data.shares)
    return status_message_response(success, msg)


@portfolio_router.put('/{code}')
async def update_stock(code: str, data: StockUpdate):
    logger.info(f'PUT /api/portfolio/{code}')
    success = await StockRepository.update(code, data.name, data.cost_price, data.shares)
    return status_message_response(success, '更新成功', '更新失败')


@portfolio_router.delete('/{code}')
async def delete_stock(code: str):
    logger.info(f'DELETE /api/portfolio/{code}')
    success = await StockRepository.delete(code)
    return status_message_response(success, '删除成功', '删除失败')
