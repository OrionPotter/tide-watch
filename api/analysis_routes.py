from fastapi import APIRouter, HTTPException

from schemas.analysis import AnalysisRequest
from services.price_action_service import PriceActionService
from utils.api_helpers import current_timestamp, success_response
from utils.logger import get_logger

logger = get_logger('analysis_routes')
analysis_router = APIRouter()


@analysis_router.get('')
async def list_analysis_reports():
    logger.info('GET /api/analysis')
    reports = await PriceActionService.list_reports()
    return success_response(timestamp=current_timestamp(), data={'reports': reports})


@analysis_router.get('/{report_id}')
async def get_analysis_report(report_id: int):
    logger.info(f'GET /api/analysis/{report_id}')
    report = await PriceActionService.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail='分析记录不存在')
    return success_response(timestamp=current_timestamp(), data={'report': report})


@analysis_router.post('')
async def create_analysis_report(payload: AnalysisRequest):
    logger.info(f'POST /api/analysis {payload.code}')
    try:
        result = await PriceActionService.generate_analysis(
            code=payload.code,
            count=payload.count,
            period=payload.period,
        )
        return success_response(timestamp=current_timestamp(), data=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f'POST /api/analysis failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))
