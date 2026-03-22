from __future__ import annotations

from typing import Any

from services.portfolio_service import PortfolioService
from services.xueqiu_service import XueqiuService


class DashboardService:
    @staticmethod
    async def _get_xueqiu_updates(limit: int = 5) -> list[dict[str, Any]]:
        try:
            all_data = await XueqiuService.get_all_formatted_data_async()
        except Exception:
            return []

        updates: list[dict[str, Any]] = []
        for cube_symbol, history in all_data.items():
            if not history:
                continue
            latest = history[0]
            updates.append(
                {
                    'cube_symbol': cube_symbol,
                    'cube_name': latest.get('cube_name', cube_symbol),
                    'rebalancing_time': latest.get('rebalancing_time'),
                    'comment': latest.get('comment', ''),
                    'change_count': latest.get('total_change_count', 0),
                    'top_changes': (latest.get('changes') or [])[:3],
                }
            )

        updates.sort(key=lambda item: item.get('rebalancing_time') or '', reverse=True)
        return updates[:limit]

    @staticmethod
    async def get_dashboard_data(monitor_stocks: list[dict[str, Any]]) -> dict[str, Any]:
        portfolio_rows, portfolio_summary = await PortfolioService.get_portfolio_data()

        focus_stocks = sorted(
            [stock for stock in monitor_stocks if stock.get('is_focus')],
            key=lambda item: (item.get('score', 0), item.get('is_holding', False)),
            reverse=True,
        )[:10]
        buy_candidates = sorted(
            [stock for stock in monitor_stocks if stock.get('is_buy_candidate')],
            key=lambda item: (item.get('score', 0), item.get('current_price', 0)),
            reverse=True,
        )[:8]
        risk_stocks = sorted(
            [stock for stock in monitor_stocks if stock.get('is_risk_stock')],
            key=lambda item: (item.get('risk_level') == 'high', item.get('is_holding', False), item.get('score', 0)),
            reverse=True,
        )[:8]

        return {
            'portfolio_summary': portfolio_summary,
            'portfolio_rows': portfolio_rows[:8],
            'focus_stocks': focus_stocks,
            'buy_candidates': buy_candidates,
            'risk_stocks': risk_stocks,
            'xueqiu_updates': await DashboardService._get_xueqiu_updates(),
            'system_status': {
                'holding_count': len(portfolio_rows),
                'monitor_count': len(monitor_stocks),
                'focus_count': len(focus_stocks),
            },
        }
