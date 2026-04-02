from unittest.mock import AsyncMock, patch


class TestDashboardRoutes:
    def test_get_dashboard_success(self, client):
        monitor_stocks = [
            {
                'code': 'sh600519',
                'name': '贵州茅台',
                'score': 85,
                'is_focus': True,
                'is_buy_candidate': True,
                'is_risk_stock': False,
                'is_holding': True,
                'current_price': 1688.0,
                'action_label': '可分批',
                'risk_level': 'low',
                'reason_tags': ['低估', '多头'],
            }
        ]
        dashboard_data = {
            'portfolio_summary': {
                'market_value': 100000.0,
                'profit': 8000.0,
                'annual_dividend': 1200.0,
            },
            'portfolio_rows': [
                {
                    'code': 'sh600519',
                    'name': '贵州茅台',
                    'current_price': 1688.0,
                    'cost_price': 1500.0,
                    'market_value': 84400.0,
                    'profit': 9400.0,
                }
            ],
            'focus_stocks': monitor_stocks,
            'buy_candidates': monitor_stocks,
            'risk_stocks': [],
            'system_status': {
                'holding_count': 1,
                'monitor_count': 1,
                'focus_count': 1,
            },
        }

        with patch('services.monitor_service.MonitorService.get_enriched_monitor_data', new_callable=AsyncMock) as mock_monitor, \
             patch('services.dashboard_service.DashboardService.get_dashboard_data', new_callable=AsyncMock) as mock_dashboard:
            mock_monitor.return_value = monitor_stocks
            mock_dashboard.return_value = dashboard_data

            response = client.get('/api/dashboard')

            assert response.status_code == 200
            payload = response.json()
            assert payload['status'] == 'success'
            assert payload['data']['portfolio_summary']['market_value'] == 100000.0
            assert payload['data']['focus_stocks'][0]['name'] == '贵州茅台'
            mock_monitor.assert_called_once()
            mock_dashboard.assert_called_once_with(monitor_stocks)

    def test_get_dashboard_failure(self, client):
        with patch('services.monitor_service.MonitorService.get_enriched_monitor_data', new_callable=AsyncMock) as mock_monitor:
            mock_monitor.side_effect = RuntimeError('dashboard failed')

            response = client.get('/api/dashboard')

            assert response.status_code == 500
            assert response.json()['detail'] == 'dashboard failed'
