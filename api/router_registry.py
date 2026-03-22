from fastapi import FastAPI

from api.admin_routes import admin_router
from api.industry_board_routes import industry_board_router
from api.monitor_routes import monitor_router
from api.portfolio_routes import portfolio_router
from api.stock_list_routes import stock_list_router
from api.tools_routes import tools_router
from api.xueqiu_routes import xueqiu_router

ROUTERS = (
    (portfolio_router, '/api/portfolio', 'portfolio'),
    (monitor_router, '/api/monitor', 'monitor'),
    (admin_router, '/api/admin', 'admin'),
    (tools_router, '/api/tools', 'tools'),
    (xueqiu_router, '/api/xueqiu', 'xueqiu'),
    (stock_list_router, '/api/stock-list', 'stock-list'),
    (industry_board_router, '/api/industry-board', 'industry-board'),
)


def register_api_routers(app: FastAPI) -> None:
    for router, prefix, tag in ROUTERS:
        app.include_router(router, prefix=prefix, tags=[tag])
