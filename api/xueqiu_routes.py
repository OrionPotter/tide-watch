import time

from fastapi import APIRouter, HTTPException

from services.xueqiu_service import XueqiuService
from utils.api_helpers import current_timestamp, success_response
from utils.logger import get_logger

logger = get_logger('xueqiu_routes')

xueqiu_router = APIRouter()


@xueqiu_router.get('')
async def get_xueqiu_data():
    start_time = time.time()
    logger.info('GET /api/xueqiu')
    try:
        all_data = await XueqiuService.get_all_formatted_data_async()
        logger.info(f'GET /api/xueqiu completed in {time.time() - start_time:.2f}s')
        return success_response(timestamp=current_timestamp(), data=all_data, clean_nan=True)
    except Exception as exc:
        logger.error(f'GET /api/xueqiu failed after {time.time() - start_time:.2f}s: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))


@xueqiu_router.get('/{cube_symbol}')
async def get_cube_data(cube_symbol: str):
    logger.info(f'GET /api/xueqiu/{cube_symbol}')
    try:
        import aiohttp
        from repositories.xueqiu_repository import XueqiuCubeRepository

        headers = XueqiuService._get_headers()
        async with aiohttp.ClientSession(headers=headers, trust_env=False) as session:
            history = await XueqiuService._fetch_cube_data(session, cube_symbol)

        if history is None:
            raise HTTPException(status_code=500, detail='获取数据失败')

        cube = await XueqiuCubeRepository.get_by_symbol(cube_symbol)
        cube_name = cube.cube_name if cube else cube_symbol
        formatted = XueqiuService.format_rebalancing_data(cube_symbol, cube_name, history)
        return success_response(
            timestamp=current_timestamp(),
            cube_symbol=cube_symbol,
            data=formatted,
            clean_nan=True,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f'GET /api/xueqiu/{cube_symbol} failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))
