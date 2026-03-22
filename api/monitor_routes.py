import threading
import time

from api.route_helpers import bool_status_response
from fastapi import APIRouter, HTTPException
from schemas.monitor import MonitorStockCreate, MonitorStockUpdate, ToggleStock, UpdateKline
from services.monitor_service import MonitorService
from utils.api_helpers import current_timestamp, success_response
from utils.logger import get_logger

logger = get_logger('monitor_routes')

monitor_router = APIRouter()

_monitor_cache = {
    'data': None,
    'timestamp': None,
    'lock': threading.Lock(),
}
_CACHE_TTL = 60


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

        stocks = await MonitorService.get_enriched_monitor_data()
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
    return bool_status_response(success, msg, msg)


@monitor_router.put('/stocks/{code}')
async def update_monitor_stock(code: str, data: MonitorStockUpdate):
    success, msg = await MonitorService.update_monitor_stock(
        code,
        data.name,
        data.timeframe,
        data.reasonable_pe_min,
        data.reasonable_pe_max,
    )
    return bool_status_response(success, msg, msg)


@monitor_router.delete('/stocks/{code}')
async def delete_monitor_stock(code: str):
    success, msg = await MonitorService.delete_monitor_stock(code)
    return bool_status_response(success, msg, msg)


@monitor_router.post('/stocks/{code}/toggle')
async def toggle_monitor_stock(code: str, data: ToggleStock):
    success, msg = await MonitorService.toggle_monitor_stock(code, data.enabled)
    return bool_status_response(success, msg, msg)


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
