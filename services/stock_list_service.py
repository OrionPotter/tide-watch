import akshare as ak
from datetime import datetime

from repositories.stock_list_repository import StockListRepository
from services.service_helpers import clear_proxy_env, run_async
from utils.logger import get_logger

clear_proxy_env()
logger = get_logger('stock_list_service')


class StockListService:
    """股票代码服务（异步版本）"""

    @staticmethod
    def fetch_stock_list_from_akshare():
        logger.info('开始从 akshare 获取沪深京 A 股列表')
        try:
            df = ak.stock_zh_a_spot_em()
            stock_list = df[['代码', '名称']].copy()
            stock_list.columns = ['code', 'name']
            result = stock_list.to_dict('records')
            logger.info(f'成功获取 {len(result)} 只股票')
            return result
        except Exception as exc:
            logger.error(f'从 akshare 获取股票列表失败: {exc}')
            return None

    @staticmethod
    async def update_stock_list_async():
        logger.info('开始更新股票列表')
        start_time = datetime.now()
        stock_list = StockListService.fetch_stock_list_from_akshare()
        if stock_list is None:
            logger.error('获取股票列表失败，更新终止')
            return False, '获取股票列表失败'

        success, result = await StockListRepository.batch_upsert(stock_list)
        if success:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f'股票列表更新成功，共 {result} 条记录，耗时: {elapsed:.2f}s')
            return True, f'更新成功，共 {result} 条记录'

        logger.error(f'股票列表更新失败: {result}')
        return False, f'更新失败: {result}'

    @staticmethod
    def update_stock_list():
        return run_async(StockListService.update_stock_list_async)

    @staticmethod
    async def get_all_stocks_async():
        return await StockListRepository.get_all()

    @staticmethod
    def get_all_stocks():
        return run_async(StockListService.get_all_stocks_async)

    @staticmethod
    async def get_stock_by_code_async(code):
        return await StockListRepository.get_by_code(code)

    @staticmethod
    def get_stock_by_code(code):
        return run_async(lambda: StockListService.get_stock_by_code_async(code))

    @staticmethod
    async def search_stocks_async(keyword):
        return await StockListRepository.search_by_name(keyword)

    @staticmethod
    def search_stocks(keyword):
        return run_async(lambda: StockListService.search_stocks_async(keyword))

    @staticmethod
    async def get_stock_count_async():
        return await StockListRepository.get_count()

    @staticmethod
    def get_stock_count():
        return run_async(StockListService.get_stock_count_async)

    @staticmethod
    async def auto_update_stock_list_async():
        logger.info('定时任务：自动更新股票列表')
        try:
            success, message = await StockListService.update_stock_list_async()
            if success:
                logger.info(f'定时任务完成: {message}')
            else:
                logger.error(f'定时任务失败: {message}')
        except Exception as exc:
            logger.error(f'定时任务异常: {exc}')

    @staticmethod
    def auto_update_stock_list():
        run_async(StockListService.auto_update_stock_list_async)
