from repositories.monitor_repository import MonitorStockRepository
from repositories.portfolio_repository import StockRepository
from services.data_service import DataService
from services.monitor_scoring_service import MonitorScoringService
from services.service_helpers import clear_proxy_env, success_or_failure

clear_proxy_env()


class MonitorService:
    """监控业务逻辑"""

    @staticmethod
    async def get_monitor_data():
        return await DataService.get_monitor_data()

    @staticmethod
    async def get_enriched_monitor_data():
        stocks = await DataService.get_monitor_data()
        holdings = await StockRepository.get_all()
        holding_codes = {stock.code for stock in holdings}

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
            MonitorScoringService.score_stock(stock, holding_codes)

        stocks.sort(
            key=lambda item: (
                item.get('score', 0),
                item.get('is_holding', False),
                item.get('current_price', 0),
            ),
            reverse=True,
        )
        return stocks

    @staticmethod
    async def get_all_monitor_stocks():
        stocks = await MonitorStockRepository.get_all()
        return [stock.to_dict() for stock in stocks]

    @staticmethod
    async def get_monitor_stock(code):
        stock = await MonitorStockRepository.get_by_code(code)
        return stock.to_dict() if stock else None

    @staticmethod
    async def create_monitor_stock(code, name, timeframe, pe_min=15, pe_max=20):
        return await MonitorStockRepository.add(code, name, timeframe, pe_min, pe_max)

    @staticmethod
    async def update_monitor_stock(code, name, timeframe, pe_min, pe_max):
        success = await MonitorStockRepository.update(code, name, timeframe, pe_min, pe_max)
        return success_or_failure(success, '更新成功', '更新失败')

    @staticmethod
    async def delete_monitor_stock(code):
        success = await MonitorStockRepository.delete(code)
        return success_or_failure(success, '删除成功', '删除失败')

    @staticmethod
    async def toggle_monitor_stock(code, enabled):
        success = await MonitorStockRepository.toggle_enabled(code, enabled)
        return success_or_failure(success, '操作成功', '操作失败')

    @staticmethod
    def calculate_reasonable_price(eps_forecast, pe_min, pe_max):
        if not eps_forecast:
            return None, None
        return round(eps_forecast * pe_min, 2), round(eps_forecast * pe_max, 2)

    @staticmethod
    def check_valuation_status(current_price, eps_forecast, pe_min, pe_max):
        if not eps_forecast:
            return '未知'

        min_price = eps_forecast * pe_min
        max_price = eps_forecast * pe_max
        if current_price < min_price:
            return '低估'
        if current_price > max_price:
            return '高估'
        return '正常'

    @staticmethod
    def check_technical_status(current_price, ema144, ema188):
        if not ema144 or not ema188:
            return '无信号'

        min_ema = min(ema144, ema188)
        max_ema = max(ema144, ema188)
        if current_price < min_ema:
            return '破位'
        if min_ema <= current_price <= max_ema:
            return '加仓'
        return '无信号'

    @staticmethod
    def check_trend(ema_dict, timeframe):
        if timeframe == '1d':
            ema5, ema10, ema20 = ema_dict.get('ema5'), ema_dict.get('ema10'), ema_dict.get('ema20')
            if ema5 and ema10 and ema20:
                if ema5 > ema10 > ema20:
                    return '多头'
                if ema5 < ema10 < ema20:
                    return '空头'
                return '震荡'

        if timeframe == '2d':
            ema10, ema30, ema60 = ema_dict.get('ema10'), ema_dict.get('ema30'), ema_dict.get('ema60')
            if ema10 and ema30 and ema60:
                if ema10 > ema30 > ema60:
                    return '多头'
                if ema10 < ema30 < ema60:
                    return '空头'
                return '震荡'

        if timeframe == '3d':
            ema7, ema21, ema42 = ema_dict.get('ema7'), ema_dict.get('ema21'), ema_dict.get('ema42')
            if ema7 and ema21 and ema42:
                if ema7 > ema21 > ema42:
                    return '多头'
                if ema7 < ema21 < ema42:
                    return '空头'
                return '震荡'

        return '未知'
