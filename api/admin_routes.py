from fastapi import APIRouter
from repositories.monitor_repository import MonitorStockRepository
from repositories.portfolio_repository import StockRepository
from schemas.admin import (
    AdminMonitorStockCreate,
    AdminMonitorStockUpdate,
    AdminStockCreate,
    AdminStockUpdate,
    ToggleEnabled,
    XueqiuCubeCreate,
    XueqiuCubeUpdate,
)
from utils.api_helpers import status_message_response, success_response
from utils.logger import get_logger

logger = get_logger('admin_routes')

admin_router = APIRouter()


@admin_router.get('/stocks')
async def list_stocks():
    logger.info('GET /api/admin/stocks')
    stocks = await StockRepository.get_all()
    return success_response(data=[stock.to_dict() for stock in stocks], clean_nan=True)


@admin_router.post('/stocks')
async def create_stock(data: AdminStockCreate):
    success, msg = await StockRepository.add(data.code, data.name, data.cost_price, data.shares)
    return status_message_response(success, msg)


@admin_router.put('/stocks/{code}')
async def update_stock(code: str, data: AdminStockUpdate):
    success = await StockRepository.update(code, data.name, data.cost_price, data.shares)
    return status_message_response(success, '更新成功', '更新失败')


@admin_router.delete('/stocks/{code}')
async def delete_stock(code: str):
    success = await StockRepository.delete(code)
    return status_message_response(success, '删除成功', '删除失败')


@admin_router.get('/monitor-stocks')
async def list_monitor_stocks():
    logger.info('GET /api/admin/monitor-stocks')
    stocks = await MonitorStockRepository.get_all()
    return success_response(data=[stock.to_dict() for stock in stocks], clean_nan=True)


@admin_router.post('/monitor-stocks')
async def create_monitor_stock(data: AdminMonitorStockCreate):
    success, msg = await MonitorStockRepository.add(
        data.code,
        data.name,
        data.timeframe,
        data.reasonable_pe_min,
        data.reasonable_pe_max,
    )
    return status_message_response(success, msg)


@admin_router.put('/monitor-stocks/{code}')
async def update_monitor_stock(code: str, data: AdminMonitorStockUpdate):
    success = await MonitorStockRepository.update(
        code,
        data.name,
        data.timeframe,
        data.reasonable_pe_min,
        data.reasonable_pe_max,
    )
    return status_message_response(success, '更新成功', '更新失败')


@admin_router.delete('/monitor-stocks/{code}')
async def delete_monitor_stock(code: str):
    success = await MonitorStockRepository.delete(code)
    return status_message_response(success, '删除成功', '删除失败')


@admin_router.post('/monitor-stocks/{code}/toggle')
async def toggle_monitor_stock(code: str, data: ToggleEnabled):
    success = await MonitorStockRepository.toggle_enabled(code, data.enabled)
    return status_message_response(success, '操作成功', '操作失败')


@admin_router.get('/xueqiu-cubes')
async def list_xueqiu_cubes():
    from repositories.xueqiu_repository import XueqiuCubeRepository

    cubes = await XueqiuCubeRepository.get_all()
    return success_response(data=[cube.to_dict() for cube in cubes], clean_nan=True)


@admin_router.post('/xueqiu-cubes')
async def create_xueqiu_cube(data: XueqiuCubeCreate):
    from repositories.xueqiu_repository import XueqiuCubeRepository

    success, msg = await XueqiuCubeRepository.add(data.cube_symbol, data.cube_name, data.enabled)
    return status_message_response(success, msg)


@admin_router.put('/xueqiu-cubes/{cube_symbol}')
async def update_xueqiu_cube(cube_symbol: str, data: XueqiuCubeUpdate):
    from repositories.xueqiu_repository import XueqiuCubeRepository

    success = await XueqiuCubeRepository.update(cube_symbol, data.cube_name, data.enabled)
    return status_message_response(success, '更新成功', '更新失败')


@admin_router.delete('/xueqiu-cubes/{cube_symbol}')
async def delete_xueqiu_cube(cube_symbol: str):
    from repositories.xueqiu_repository import XueqiuCubeRepository

    success = await XueqiuCubeRepository.delete(cube_symbol)
    return status_message_response(success, '删除成功', '删除失败')


@admin_router.post('/xueqiu-cubes/{cube_symbol}/toggle')
async def toggle_xueqiu_cube(cube_symbol: str, data: ToggleEnabled):
    from repositories.xueqiu_repository import XueqiuCubeRepository

    success = await XueqiuCubeRepository.toggle_enabled(cube_symbol, data.enabled)
    return status_message_response(success, '操作成功', '操作失败')
