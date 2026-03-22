import threading
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.monitor_service import MonitorService
from utils.api_helpers import current_timestamp, status_message_response, success_response
from utils.logger import get_logger

logger = get_logger('monitor_routes')

monitor_router = APIRouter()

_monitor_cache = {
    'data': None,
    'timestamp': None,
    'lock': threading.Lock(),
}
_CACHE_TTL = 60


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


@monitor_router.get('')
async def get_monitor():
    logger.info('GET /api/monitor')
    try:
        current_time = time.time()
        with _monitor_cache['lock']:
            if (
                _monitor_cache['data'] is not None
                and _monitor_cache['timestamp'] is not None
                and current_time - _monitor_cache['timestamp'] < _CACHE_TTL
            ):
                return _monitor_cache['data']

        stocks = await MonitorService.get_monitor_data()
        for stock in stocks:
            min_price, max_price = MonitorService.calculate_reasonable_price(
                stock.get('eps_forecast'),
                stock.get('reasonable_pe_min'),
                stock.get('reasonable_pe_max'),
            )
            stock['reasonable_price_min'] = min_price
            stock['reasonable_price_max'] = max_price
            stock['valuation_status'] = MonitorService.check_valuation_status(
                stock.get('current_price'),
                stock.get('eps_forecast'),
                stock.get('reasonable_pe_min'),
                stock.get('reasonable_pe_max'),
            )
            stock['technical_status'] = MonitorService.check_technical_status(
                stock.get('current_price'),
                stock.get('ema144'),
                stock.get('ema188'),
            )
            stock['trend'] = MonitorService.check_trend(
                {
                    'ema5': stock.get('ema5'),
                    'ema10': stock.get('ema10'),
                    'ema20': stock.get('ema20'),
                    'ema30': stock.get('ema30'),
                    'ema60': stock.get('ema60'),
                    'ema7': stock.get('ema7'),
                    'ema21': stock.get('ema21'),
                    'ema42': stock.get('ema42'),
                },
                stock.get('timeframe'),
            )

        result = success_response(timestamp=current_timestamp(), stocks=stocks, clean_nan=True)
        with _monitor_cache['lock']:
            _monitor_cache['data'] = result
            _monitor_cache['timestamp'] = current_time
        return result
    except Exception as exc:
        logger.error(f'GET /api/monitor failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))


@monitor_router.get('/stocks')
async def list_monitor_stocks():
    try:
        stocks = await MonitorService.get_all_monitor_stocks()
        return success_response(data=stocks)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@monitor_router.post('/stocks')
async def create_monitor_stock(data: MonitorStockCreate):
    success, msg = await MonitorService.create_monitor_stock(
        data.code,
        data.name,
        data.timeframe,
        data.reasonable_pe_min,
        data.reasonable_pe_max,
    )
    return status_message_response(success, msg)


@monitor_router.put('/stocks/{code}')
async def update_monitor_stock(code: str, data: MonitorStockUpdate):
    success, msg = await MonitorService.update_monitor_stock(
        code,
        data.name,
        data.timeframe,
        data.reasonable_pe_min,
        data.reasonable_pe_max,
    )
    return status_message_response(success, msg)


@monitor_router.delete('/stocks/{code}')
async def delete_monitor_stock(code: str):
    success, msg = await MonitorService.delete_monitor_stock(code)
    return status_message_response(success, msg)


@monitor_router.post('/stocks/{code}/toggle')
async def toggle_monitor_stock(code: str, data: ToggleStock):
    success, msg = await MonitorService.toggle_monitor_stock(code, data.enabled)
    return status_message_response(success, msg)


@monitor_router.post('/update-kline')
async def update_kline(data: UpdateKline):
    try:
        import asyncio
        from services.kline_service import KlineService

        asyncio.create_task(
            KlineService.batch_update_kline_async(force_update=data.force_update, max_concurrent=3)
        )
        return success_response(message='K线更新任务已启动')
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
