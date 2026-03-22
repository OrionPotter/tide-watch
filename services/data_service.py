import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import os
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import asyncio
import time
from dotenv import load_dotenv
from repositories.cache_repository import MonitorDataCacheRepository
from repositories.eps_cache_repository import EpsCacheRepository
from utils.logger import get_logger

load_dotenv()

os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('all_proxy', None)

logger = get_logger('data_service')


class DataService:
    """数据获取服务"""

    @staticmethod
    def calculate_ema(prices, period):
        if len(prices) < period:
            return None
        if not isinstance(prices, pd.Series):
            prices = pd.Series(prices)
        ema = prices.ewm(span=period, adjust=False).mean()
        return round(ema.iloc[-1], 2)

    @staticmethod
    async def get_stock_kline_data(stock_code, period='daily', count=250):
        from services.kline_service import KlineService

        df = await KlineService.get_kline_with_cache(stock_code, period, count)
        if df is not None:
            return df

        try:
            if stock_code.startswith('sh'):
                symbol = 'sh' + stock_code[2:]
            elif stock_code.startswith('sz'):
                symbol = 'sz' + stock_code[2:]
            else:
                symbol = 'sh' + stock_code if stock_code.startswith('6') else 'sz' + stock_code

            logger.info(f'使用 API 获取 {stock_code} 的 K 线数据')
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zh_a_hist_tx(symbol=symbol, start_date='20200101', end_date='20500101', adjust='qfq')
            )

            if df is None or df.empty:
                logger.warning(f'获取 {stock_code} K 线数据为空')
                return None

            if period == '2d':
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                df = df.resample('2B').agg({
                    'open': 'first', 'close': 'last', 'high': 'max', 'low': 'min', 'amount': 'sum'
                }).dropna()
                df = df.reset_index()
                df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            elif period == '3d':
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                df = df.resample('3B').agg({
                    'open': 'first', 'close': 'last', 'high': 'max', 'low': 'min', 'amount': 'sum'
                }).dropna()
                df = df.reset_index()
                df['date'] = df['date'].dt.strftime('%Y-%m-%d')

            if 'date' in df.columns and 'close' in df.columns:
                df = df.rename(columns={'date': '日期', 'open': '开盘', 'close': '收盘', 'high': '最高', 'low': '最低'})

            if len(df) > count:
                df = df.tail(count)
            return df
        except Exception as exc:
            logger.error(f'获取 {stock_code} K 线数据失败: {exc}')
            return None

    @staticmethod
    async def get_eps_forecast_async(stock_code):
        eps_value = await EpsCacheRepository.get(stock_code)
        if eps_value is not None:
            return eps_value

        code = DataService._strip_exchange_prefix(stock_code)
        try:
            from services.eps_service import get_current_year_eps_forecast
            eps = get_current_year_eps_forecast(code)
            if eps is not None:
                await EpsCacheRepository.set(stock_code, eps)
            return eps
        except Exception as exc:
            logger.error(f'获取 {stock_code} EPS 预测失败: {exc}')
            return None

    @staticmethod
    def get_eps_forecast_sync(stock_code):
        code = DataService._strip_exchange_prefix(stock_code)
        try:
            from services.eps_service import get_current_year_eps_forecast
            return get_current_year_eps_forecast(code)
        except Exception as exc:
            logger.error(f'获取 {stock_code} EPS 预测失败: {exc}')
            return None

    @staticmethod
    def get_eps_forecast(stock_code):
        return asyncio.run(DataService.get_eps_forecast_async(stock_code))

    @staticmethod
    def _strip_exchange_prefix(stock_code):
        if stock_code.startswith('sh') or stock_code.startswith('sz'):
            return stock_code[2:]
        return stock_code

    @staticmethod
    def _get_reasonable_pe_range(monitor_config):
        return (
            monitor_config.reasonable_pe_min if monitor_config else 15,
            monitor_config.reasonable_pe_max if monitor_config else 20,
        )

    @staticmethod
    def _build_monitor_result(stock_code, stock_name, timeframe, current_price, monitor_config, ema_values, eps_forecast=None):
        pe_min, pe_max = DataService._get_reasonable_pe_range(monitor_config)
        return {
            'code': stock_code,
            'name': stock_name,
            'current_price': round(current_price, 2),
            'ema144': ema_values['ema144'],
            'ema188': ema_values['ema188'],
            'ema5': ema_values['ema5'],
            'ema10': ema_values['ema10'],
            'ema20': ema_values['ema20'],
            'ema30': ema_values['ema30'],
            'ema60': ema_values['ema60'],
            'ema7': ema_values['ema7'],
            'ema21': ema_values['ema21'],
            'ema42': ema_values['ema42'],
            'eps_forecast': eps_forecast,
            'timeframe': timeframe,
            'reasonable_pe_min': pe_min,
            'reasonable_pe_max': pe_max,
        }

    @staticmethod
    def _extract_cached_monitor_result(stock, monitor_config, cached):
        return {
            'code': stock.code,
            'name': stock.name,
            'current_price': cached.current_price,
            'ema144': cached.ema144,
            'ema188': cached.ema188,
            'ema5': cached.ema5,
            'ema10': cached.ema10,
            'ema20': cached.ema20,
            'ema30': cached.ema30,
            'ema60': cached.ema60,
            'ema7': cached.ema7,
            'ema21': cached.ema21,
            'ema42': cached.ema42,
            'eps_forecast': cached.eps_forecast,
            'timeframe': stock.timeframe,
            'reasonable_pe_min': monitor_config.reasonable_pe_min if monitor_config else 15,
            'reasonable_pe_max': monitor_config.reasonable_pe_max if monitor_config else 20,
        }

    @staticmethod
    def _calculate_trend_emas(closing_prices, timeframe):
        values = {
            'ema5': None,
            'ema10': None,
            'ema20': None,
            'ema30': None,
            'ema60': None,
            'ema7': None,
            'ema21': None,
            'ema42': None,
        }
        if timeframe == '1d' and len(closing_prices) >= 20:
            values['ema5'] = DataService.calculate_ema(closing_prices, 5)
            values['ema10'] = DataService.calculate_ema(closing_prices, 10)
            values['ema20'] = DataService.calculate_ema(closing_prices, 20)
        elif timeframe == '2d' and len(closing_prices) >= 60:
            values['ema10'] = DataService.calculate_ema(closing_prices, 10)
            values['ema30'] = DataService.calculate_ema(closing_prices, 30)
            values['ema60'] = DataService.calculate_ema(closing_prices, 60)
        elif timeframe == '3d' and len(closing_prices) >= 42:
            values['ema7'] = DataService.calculate_ema(closing_prices, 7)
            values['ema21'] = DataService.calculate_ema(closing_prices, 21)
            values['ema42'] = DataService.calculate_ema(closing_prices, 42)
        return values

    @staticmethod
    def _build_monitor_result_from_market_data(stock, monitor_config, kline_data, current_price, eps_forecast=None):
        stock_code = stock.code
        stock_name = stock.name
        timeframe = stock.timeframe

        if current_price is None:
            logger.warning(f'无法获取 {stock_code} 的当前价格')
            return None
        if kline_data is None or len(kline_data) < 188:
            logger.warning(f'无法获取 {stock_code} 的足够 K 线数据')
            return None

        closing_prices = kline_data['收盘']
        ema144 = DataService.calculate_ema(closing_prices, 144)
        ema188 = DataService.calculate_ema(closing_prices, 188)
        if ema144 is None or ema188 is None:
            logger.warning(f'无法计算 {stock_code} 的 EMA 值')
            return None

        ema_values = DataService._calculate_trend_emas(closing_prices, timeframe)
        ema_values['ema144'] = ema144
        ema_values['ema188'] = ema188
        return DataService._build_monitor_result(
            stock_code, stock_name, timeframe, current_price, monitor_config, ema_values, eps_forecast
        )

    @staticmethod
    async def process_monitor_stock_with_data(stock, monitor_config, kline_data, current_price):
        try:
            return DataService._build_monitor_result_from_market_data(stock, monitor_config, kline_data, current_price)
        except Exception as exc:
            logger.error(f'处理 {stock.code} 时出错: {exc}')
            return None

    @staticmethod
    async def process_monitor_stock_uncached_with_kline(stock, monitor_config, kline_data):
        from services.portfolio_service import PortfolioService
        try:
            _, current_price, _, _ = await PortfolioService.get_real_time_price_async(stock.code)
            return DataService._build_monitor_result_from_market_data(stock, monitor_config, kline_data, current_price)
        except Exception as exc:
            logger.error(f'处理 {stock.code} 时出错: {exc}')
            return None

    @staticmethod
    async def process_monitor_stock_uncached(stock, monitor_config):
        from services.portfolio_service import PortfolioService
        try:
            _, current_price, _, _ = await PortfolioService.get_real_time_price_async(stock.code)
            kline_data = await DataService.get_stock_kline_data(stock.code, stock.timeframe)
            return DataService._build_monitor_result_from_market_data(
                stock,
                monitor_config,
                kline_data,
                current_price,
                DataService.get_eps_forecast(stock.code),
            )
        except Exception as exc:
            logger.error(f'处理 {stock.code} 时出错: {exc}')
            return None

    @staticmethod
    async def process_monitor_stock(stock, monitor_config):
        from services.portfolio_service import PortfolioService
        try:
            cached = await MonitorDataCacheRepository.get_by_code_and_timeframe(stock.code, stock.timeframe, 30)
            if cached:
                return DataService._extract_cached_monitor_result(stock, monitor_config, cached)

            _, current_price, _, _ = await PortfolioService.get_real_time_price_async(stock.code)
            kline_data = await DataService.get_stock_kline_data(stock.code, stock.timeframe)
            return DataService._build_monitor_result_from_market_data(stock, monitor_config, kline_data, current_price)
        except Exception as exc:
            logger.error(f'处理 {stock.code} 时出错: {exc}')
            return None

    @staticmethod
    async def get_monitor_data():
        start_time = time.time()
        logger.info('开始获取监控数据...')
        from repositories.monitor_repository import MonitorStockRepository
        from repositories.kline_repository import KlineRepository
        from services.portfolio_service import PortfolioService

        deleted = await MonitorDataCacheRepository.clean_old_data(1)
        if deleted > 0:
            logger.info(f'清理了 {deleted} 条过期缓存')

        monitor_stocks = await MonitorStockRepository.get_enabled()
        logger.info(f'从数据库加载了 {len(monitor_stocks)} 只监控股票')

        code_timeframe_pairs = [(stock.code, stock.timeframe) for stock in monitor_stocks]
        cache_results = await MonitorDataCacheRepository.get_batch_by_code_and_timeframe(code_timeframe_pairs, 30)

        cached_results = []
        uncached_stocks = []
        for stock in monitor_stocks:
            key = (stock.code, stock.timeframe)
            if key in cache_results:
                cached_results.append(DataService._extract_cached_monitor_result(stock, stock, cache_results[key]))
            else:
                uncached_stocks.append(stock)

        logger.info(f'从缓存获取 {len(cached_results)} 只股票，需要重新获取 {len(uncached_stocks)} 只股票')

        if uncached_stocks:
            uncached_codes = [stock.code for stock in uncached_stocks]
            kline_data_dict = await KlineRepository.get_batch_by_codes(uncached_codes, limit=1000)

            price_start = time.time()
            price_tasks = [PortfolioService.get_real_time_price_async(stock.code) for stock in uncached_stocks]
            price_results = await asyncio.gather(*price_tasks, return_exceptions=True)

            price_map = {}
            for stock, result in zip(uncached_stocks, price_results):
                if isinstance(result, Exception):
                    logger.error(f'获取 {stock.code} 实时价格失败: {result}')
                    price_map[stock.code] = None
                else:
                    price_map[stock.code] = result[1]

            logger.info(f'批量获取 {len(uncached_stocks)} 只股票实时价格，耗时: {time.time() - price_start:.2f}s')

            process_start = time.time()
            tasks = [
                DataService.process_monitor_stock_with_data(stock, stock, kline_data_dict.get(stock.code), price_map.get(stock.code))
                for stock in uncached_stocks
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f'并发处理 {len(uncached_stocks)} 只股票，耗时: {time.time() - process_start:.2f}s')

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f'处理异常: {result}')
                elif result:
                    cached_results.append(result)
                    logger.debug(f"成功处理 {result['code']} {result['name']}")

        cache_save_start = time.time()
        cache_data_list = []
        for result in cached_results:
            cache_data_list.append({
                'code': result['code'],
                'timeframe': result['timeframe'],
                'current_price': result['current_price'],
                'ema144': result['ema144'],
                'ema188': result['ema188'],
                'ema5': result['ema5'],
                'ema10': result['ema10'],
                'ema20': result['ema20'],
                'ema30': result['ema30'],
                'ema60': result['ema60'],
                'ema7': result['ema7'],
                'ema21': result['ema21'],
                'ema42': result['ema42'],
                'eps_forecast': result['eps_forecast']
            })

        if cache_data_list:
            await MonitorDataCacheRepository.save_batch(cache_data_list)
            logger.info(f'批量保存缓存数据，耗时: {time.time() - cache_save_start:.2f}s')

        all_stocks_need_eps = [result for result in cached_results if result.get('eps_forecast') is None]
        if all_stocks_need_eps:
            eps_start = time.time()
            logger.info(f'开始批量获取 {len(all_stocks_need_eps)} 只股票的 EPS 预测...')
            codes = [result['code'] for result in all_stocks_need_eps]
            cached_eps = await EpsCacheRepository.get_batch(codes)

            cached_stocks = []
            uncached_eps_stocks = []
            for stock in all_stocks_need_eps:
                code = stock['code']
                if code in cached_eps:
                    stock['eps_forecast'] = cached_eps[code]
                    cached_stocks.append(stock)
                else:
                    uncached_eps_stocks.append(stock)

            logger.info(f'从缓存获取 {len(cached_stocks)} 只股票的 EPS，需要重新获取 {len(uncached_eps_stocks)} 只')
            if uncached_eps_stocks:
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor(max_workers=10) as executor:
                    eps_tasks = [
                        loop.run_in_executor(executor, DataService.get_eps_forecast_sync, stock['code'])
                        for stock in uncached_eps_stocks
                    ]
                    eps_results = await asyncio.gather(*eps_tasks, return_exceptions=True)
                    for stock, eps in zip(uncached_eps_stocks, eps_results):
                        if isinstance(eps, Exception):
                            logger.error(f"获取 {stock['code']} EPS 失败: {eps}")
                            stock['eps_forecast'] = None
                        else:
                            if eps is not None:
                                await EpsCacheRepository.set(stock['code'], eps)
                            stock['eps_forecast'] = eps

            logger.info(f'批量获取 EPS 完成，耗时: {time.time() - eps_start:.2f}s')

        elapsed = time.time() - start_time
        logger.info(f'获取监控数据完成，共 {len(cached_results)} 只股票，耗时: {elapsed:.2f}s')
        return cached_results
