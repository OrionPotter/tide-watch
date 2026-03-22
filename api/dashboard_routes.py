from fastapi import APIRouter, HTTPException

from services.dashboard_service import DashboardService
from services.monitor_service import MonitorService
from utils.api_helpers import current_timestamp, success_response
from utils.logger import get_logger

logger = get_logger('dashboard_routes')

dashboard_router = APIRouter()


@dashboard_router.get('')
async def get_dashboard():
    logger.info('GET /api/dashboard')
    try:
        monitor_stocks = await MonitorService.get_enriched_monitor_data()
        data = await DashboardService.get_dashboard_data(monitor_stocks)
        return success_response(timestamp=current_timestamp(), data=data, clean_nan=True)
    except Exception as exc:
        logger.error(f'GET /api/dashboard failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))
