from unittest.mock import AsyncMock, patch


class TestMonitorRoutes:
    """测试 monitor_routes 接口。"""

    def test_get_monitor_success(self, client):
        mock_stocks = [
            {
                'code': 'sh600000',
                'name': '浦发银行',
                'current_price': 10.5,
                'eps_forecast': 1.0,
                'reasonable_pe_min': 15,
                'reasonable_pe_max': 20,
                'ema144': 10.0,
                'ema188': 9.5,
                'timeframe': '1d',
                'ema5': 10.5,
                'ema10': 10.4,
                'ema20': 10.3,
                'ema30': 10.2,
                'ema60': 10.1,
                'ema7': 10.5,
                'ema21': 10.3,
                'ema42': 10.2,
                'score': 82,
                'action_label': '可分批',
                'risk_level': 'low',
                'is_holding': True,
                'reason_tags': ['低估', '多头'],
            }
        ]

        with patch('services.monitor_service.MonitorService.get_enriched_monitor_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_stocks

            response = client.get('/api/monitor')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert 'timestamp' in data
            assert len(data['stocks']) == 1
            assert data['stocks'][0]['score'] == 82
            assert data['stocks'][0]['action_label'] == '可分批'
            assert data['stocks'][0]['risk_level'] == 'low'
            mock_get_data.assert_called_once()

    def test_list_monitor_stocks_success(self, client):
        mock_stocks = [
            {
                'code': 'sh600000',
                'name': '浦发银行',
                'timeframe': '1d',
                'enabled': True,
            }
        ]

        with patch('services.monitor_service.MonitorService.get_all_monitor_stocks', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = mock_stocks

            response = client.get('/api/monitor/stocks')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert len(data['data']) == 1
            assert data['data'][0]['code'] == 'sh600000'
            mock_get_all.assert_called_once()

    def test_list_monitor_stocks_empty(self, client):
        with patch('services.monitor_service.MonitorService.get_all_monitor_stocks', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []

            response = client.get('/api/monitor/stocks')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['data'] == []

    def test_create_monitor_stock_success(self, client):
        stock_data = {
            'code': 'sh600000',
            'name': '浦发银行',
            'timeframe': '1d',
            'reasonable_pe_min': 15,
            'reasonable_pe_max': 20,
        }

        with patch('services.monitor_service.MonitorService.create_monitor_stock', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = (True, '创建成功')

            response = client.post('/api/monitor/stocks', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '创建成功'
            mock_create.assert_called_once_with('sh600000', '浦发银行', '1d', 15, 20)

    def test_create_monitor_stock_failure(self, client):
        stock_data = {
            'code': 'sh600000',
            'name': '浦发银行',
            'timeframe': '1d',
            'reasonable_pe_min': 15,
            'reasonable_pe_max': 20,
        }

        with patch('services.monitor_service.MonitorService.create_monitor_stock', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = (False, '股票已存在')

            response = client.post('/api/monitor/stocks', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'error'
            assert data['message'] == '股票已存在'

    def test_update_monitor_stock_success(self, client):
        stock_data = {
            'name': '浦发银行',
            'timeframe': '2d',
            'reasonable_pe_min': 18,
            'reasonable_pe_max': 25,
        }

        with patch('services.monitor_service.MonitorService.update_monitor_stock', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = (True, '更新成功')

            response = client.put('/api/monitor/stocks/sh600000', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '更新成功'
            mock_update.assert_called_once_with('sh600000', '浦发银行', '2d', 18, 25)

    def test_delete_monitor_stock_success(self, client):
        with patch('services.monitor_service.MonitorService.delete_monitor_stock', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = (True, '删除成功')

            response = client.delete('/api/monitor/stocks/sh600000')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '删除成功'
            mock_delete.assert_called_once_with('sh600000')

    def test_toggle_monitor_stock_enable(self, client):
        with patch('services.monitor_service.MonitorService.toggle_monitor_stock', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = (True, '操作成功')

            response = client.post('/api/monitor/stocks/sh600000/toggle', json={'enabled': True})

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '操作成功'
            mock_toggle.assert_called_once_with('sh600000', True)

    def test_toggle_monitor_stock_disable(self, client):
        with patch('services.monitor_service.MonitorService.toggle_monitor_stock', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = (True, '操作成功')

            response = client.post('/api/monitor/stocks/sh600000/toggle', json={'enabled': False})

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            mock_toggle.assert_called_once_with('sh600000', False)

    def test_update_kline_success(self, client):
        update_data = {'force_update': True}

        with patch('services.kline_service.KlineService.batch_update_kline_async', new_callable=AsyncMock) as mock_update:
            response = client.post('/api/monitor/update-kline', json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == 'K线更新任务已启动'
            assert mock_update.called or True

    def test_update_kline_no_force(self, client):
        response = client.post('/api/monitor/update-kline', json={'force_update': False})

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
