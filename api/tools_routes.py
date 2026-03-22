from io import BytesIO

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.api_helpers import success_response
from utils.logger import get_logger

logger = get_logger('tools_routes')

tools_router = APIRouter()

NUMERIC_PRICE_COLUMNS = ['开盘', '收盘', '最高', '最低']


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


@tools_router.post('/calculate-cost')
def calculate_cost(data: CalculateCostRequest):
    try:
        if not data.positions:
            raise HTTPException(status_code=400, detail='请提供买入记录')

        total_shares = 0
        total_cost = 0.0
        for position in data.positions:
            if position.price <= 0 or position.shares <= 0:
                raise HTTPException(status_code=400, detail='价格和股数必须大于0')
            total_shares += position.shares
            total_cost += position.price * position.shares

        if total_shares == 0:
            raise HTTPException(status_code=400, detail='总持仓数不能为0')

        return success_response(
            data={
                'total_shares': total_shares,
                'average_cost': round(total_cost / total_shares, 2),
                'total_cost': round(total_cost, 2),
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@tools_router.get('/export-kline/stocks')
async def get_export_stocks():
    logger.info('GET /api/tools/export-kline/stocks')
    try:
        from repositories.kline_repository import KlineRepository
        from repositories.monitor_repository import MonitorStockRepository

        stocks = await MonitorStockRepository.get_enabled()
        result = []
        for stock in stocks:
            result.append(
                {
                    'code': stock.code,
                    'name': stock.name,
                    'latest_date': await KlineRepository.get_latest_date(stock.code),
                }
            )

        return success_response(data=result, clean_nan=True)
    except Exception as exc:
        logger.error(f'GET /api/tools/export-kline/stocks failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))


@tools_router.post('/export-kline')
async def export_kline(data: ExportKlineRequest):
    logger.info(f'POST /api/tools/export-kline {data.code} {data.format}')
    try:
        if not data.code:
            raise HTTPException(status_code=400, detail='请选择股票')
        if data.format not in {'csv', 'excel'}:
            raise HTTPException(status_code=400, detail='不支持的导出格式')

        from repositories.kline_repository import KlineRepository
        from repositories.monitor_repository import MonitorStockRepository

        stock = await MonitorStockRepository.get_by_code(data.code)
        stock_name = stock.name if stock else data.code
        logger.info(f'export kline for {stock_name} ({data.code})')

        dataframe = await KlineRepository.export_kline_data(data.code, data.start_date, data.end_date)
        if dataframe is None or dataframe.empty:
            raise HTTPException(status_code=400, detail='没有可导出的数据')

        for column in NUMERIC_PRICE_COLUMNS:
            if column in dataframe.columns:
                dataframe[column] = dataframe[column].round(2)

        filename = _build_export_filename(data.code, data.format, data.start_date, data.end_date)
        if data.format == 'csv':
            return _stream_csv(dataframe, filename)
        return _stream_excel(dataframe, filename)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _build_export_filename(code: str, format_type: str, start_date: str | None, end_date: str | None) -> str:
    suffix = 'csv' if format_type == 'csv' else 'xlsx'
    date_parts = [part for part in (start_date, end_date) if part]
    return f"{code}-{'-'.join(date_parts)}.{suffix}" if date_parts else f'{code}.{suffix}'


def _stream_csv(dataframe: pd.DataFrame, filename: str) -> StreamingResponse:
    output = BytesIO()
    dataframe.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    response = StreamingResponse(output, media_type='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def _stream_excel(dataframe: pd.DataFrame, filename: str) -> StreamingResponse:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='K线数据')
    output.seek(0)
    response = StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response
