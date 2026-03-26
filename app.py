import asyncio
import datetime
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.router_registry import register_api_routers
from utils.db import DatabaseUnavailableError, close_db_pool, init_db_pool
from utils.logger import get_logger
from utils.template_renderer import render_page

load_dotenv()
logger = get_logger('app')


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db_pool()
        logger.info('数据库连接池已初始化')
    except DatabaseUnavailableError:
        logger.warning('数据库不可用，服务将以降级模式启动')

    start_background_tasks()

    from services.scheduler_service import SchedulerService

    SchedulerService.start()

    if os.getenv('AUTO_UPDATE_KLINE', 'true').lower() == 'true':
        from services.kline_service import KlineService

        SchedulerService.add_cron_job(
            KlineService.auto_update_kline_data,
            hour=15,
            minute=5,
            job_id='daily_kline_update',
        )

    if os.getenv('AUTO_UPDATE_STOCK_LIST', 'true').lower() == 'true':
        from services.stock_list_service import StockListService

        SchedulerService.add_cron_job(
            StockListService.auto_update_stock_list,
            hour=12,
            minute=0,
            job_id='daily_stock_list_update',
        )

    yield

    SchedulerService.shutdown()
    await close_db_pool()
    logger.info('数据库连接池已关闭')


PAGE_TEMPLATES = {
    '/': 'index.html',
    '/admin': 'admin.html',
    '/monitor': 'monitor.html',
    '/tools': 'tools.html',
    '/xueqiu': 'xueqiu.html',
}


def register_page_routes(app: FastAPI) -> None:
    for path, template_name in PAGE_TEMPLATES.items():
        async def page(request: Request, template_name: str = template_name):
            return render_page(template_name, request)

        app.get(path, response_class=HTMLResponse)(page)


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.mount('/static', StaticFiles(directory='static'), name='static')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.middleware('http')
    async def log_requests(request: Request, call_next):
        import time

        path = request.url.path
        if not path.startswith('/static'):
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 请求开始 {request.method} {path}")

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        if not path.startswith('/static'):
            print(
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 请求完成: {request.method} {path} - 状态 {response.status_code} - 耗时 {process_time:.2f}s"
            )

        return response

    @app.exception_handler(DatabaseUnavailableError)
    async def handle_database_unavailable(_: Request, exc: DatabaseUnavailableError):
        return JSONResponse(
            status_code=503,
            content={'detail': str(exc)},
        )

    register_api_routers(app)
    register_page_routes(app)
    return app


def start_background_tasks():
    if os.getenv('AUTO_UPDATE_KLINE', 'true').lower() != 'true':
        logger.warning('已禁用自动 K 线更新')
        return

    from services.kline_service import KlineService

    async def auto_update():
        try:
            await KlineService.batch_update_kline_async(force_update=False)
        except Exception as exc:
            logger.error(f'启动时自动更新 K 线失败: {exc}')

    asyncio.create_task(auto_update())
    logger.info('K 线后台更新任务已启动')


app = create_app()


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=5000)
