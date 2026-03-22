from unittest.mock import AsyncMock, MagicMock, patch


class TestAdminRoutes:
    def test_list_stocks_success(self, client):
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {
            'code': 'sh600000',
            'name': '浦发银行',
            'cost_price': 10.5,
            'shares': 1000,
        }

        with patch('repositories.portfolio_repository.StockRepository.get_all', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = [mock_stock]
            response = client.get('/api/admin/stocks')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']) == 1
        assert data['data'][0]['code'] == 'sh600000'

    def test_list_stocks_empty(self, client):
        with patch('repositories.portfolio_repository.StockRepository.get_all', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []
            response = client.get('/api/admin/stocks')

        assert response.status_code == 200
        assert response.json()['data'] == []

    def test_list_monitor_stocks_success(self, client):
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {
            'code': 'sh600000',
            'name': '浦发银行',
            'timeframe': 'daily',
            'enabled': True,
        }

        with patch('repositories.monitor_repository.MonitorStockRepository.get_all', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = [mock_stock]
            response = client.get('/api/admin/monitor-stocks')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']) == 1
        assert data['data'][0]['code'] == 'sh600000'

    def test_list_monitor_stocks_empty(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.get_all', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []
            response = client.get('/api/admin/monitor-stocks')

        assert response.status_code == 200
        assert response.json()['data'] == []

    def test_list_xueqiu_cubes_success(self, client):
        mock_cube = MagicMock()
        mock_cube.to_dict.return_value = {
            'cube_symbol': 'ZH123456',
            'cube_name': '测试组合',
            'enabled': True,
        }

        with patch('repositories.xueqiu_repository.XueqiuCubeRepository.get_all', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = [mock_cube]
            response = client.get('/api/admin/xueqiu-cubes')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']) == 1
        assert data['data'][0]['cube_symbol'] == 'ZH123456'

    def test_list_xueqiu_cubes_empty(self, client):
        with patch('repositories.xueqiu_repository.XueqiuCubeRepository.get_all', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []
            response = client.get('/api/admin/xueqiu-cubes')

        assert response.status_code == 200
        assert response.json()['data'] == []

    def test_create_stock_success(self, client):
        stock_data = {'code': 'sh600000', 'name': '浦发银行', 'cost_price': 10.5, 'shares': 1000}

        with patch('repositories.portfolio_repository.StockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, '创建成功')
            response = client.post('/api/admin/stocks', json=stock_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '创建成功'
        mock_add.assert_called_once_with('sh600000', '浦发银行', 10.5, 1000)

    def test_create_stock_failure(self, client):
        stock_data = {'code': 'sh600000', 'name': '浦发银行', 'cost_price': 10.5, 'shares': 1000}

        with patch('repositories.portfolio_repository.StockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (False, '股票已存在')
            response = client.post('/api/admin/stocks', json=stock_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'error'
        assert data['message'] == '股票已存在'

    def test_update_stock_success(self, client):
        stock_data = {'name': '浦发银行', 'cost_price': 11.0, 'shares': 1500}

        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            response = client.put('/api/admin/stocks/sh600000', json=stock_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '更新成功'
        mock_update.assert_called_once_with('sh600000', '浦发银行', 11.0, 1500)

    def test_update_stock_failure(self, client):
        stock_data = {'name': '浦发银行', 'cost_price': 11.0, 'shares': 1500}

        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = False
            response = client.put('/api/admin/stocks/sh600000', json=stock_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'error'
        assert data['message'] == '更新失败'

    def test_delete_stock_success(self, client):
        with patch('repositories.portfolio_repository.StockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            response = client.delete('/api/admin/stocks/sh600000')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '删除成功'
        mock_delete.assert_called_once_with('sh600000')

    def test_delete_stock_failure(self, client):
        with patch('repositories.portfolio_repository.StockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            response = client.delete('/api/admin/stocks/sh600000')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'error'
        assert data['message'] == '删除失败'

    def test_create_monitor_stock_success(self, client):
        stock_data = {
            'code': 'sh600000',
            'name': '浦发银行',
            'timeframe': 'daily',
            'reasonable_pe_min': 15,
            'reasonable_pe_max': 20,
        }

        with patch('repositories.monitor_repository.MonitorStockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, '创建成功')
            response = client.post('/api/admin/monitor-stocks', json=stock_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '创建成功'
        mock_add.assert_called_once_with('sh600000', '浦发银行', 'daily', 15, 20)

    def test_create_monitor_stock_with_defaults(self, client):
        stock_data = {'code': 'sh600000', 'name': '浦发银行', 'timeframe': 'daily'}

        with patch('repositories.monitor_repository.MonitorStockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, '创建成功')
            response = client.post('/api/admin/monitor-stocks', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        call_args = mock_add.call_args
        assert call_args[0][3] == 15
        assert call_args[0][4] == 20

    def test_update_monitor_stock_success(self, client):
        stock_data = {'name': '浦发银行', 'timeframe': 'weekly', 'reasonable_pe_min': 18, 'reasonable_pe_max': 25}

        with patch('repositories.monitor_repository.MonitorStockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            response = client.put('/api/admin/monitor-stocks/sh600000', json=stock_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '更新成功'
        mock_update.assert_called_once_with('sh600000', '浦发银行', 'weekly', 18, 25)

    def test_delete_monitor_stock_success(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            response = client.delete('/api/admin/monitor-stocks/sh600000')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '删除成功'
        mock_delete.assert_called_once_with('sh600000')

    def test_toggle_monitor_stock_enable(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.toggle_enabled', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = True
            response = client.post('/api/admin/monitor-stocks/sh600000/toggle', json={'enabled': True})

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '操作成功'
        mock_toggle.assert_called_once_with('sh600000', True)

    def test_toggle_monitor_stock_disable(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.toggle_enabled', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = True
            response = client.post('/api/admin/monitor-stocks/sh600000/toggle', json={'enabled': False})

        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        mock_toggle.assert_called_once_with('sh600000', False)

    def test_create_xueqiu_cube_success(self, client):
        cube_data = {'cube_symbol': 'ZH123456', 'cube_name': '测试组合', 'enabled': True}

        with patch('repositories.xueqiu_repository.XueqiuCubeRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, '创建成功')
            response = client.post('/api/admin/xueqiu-cubes', json=cube_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '创建成功'
        mock_add.assert_called_once_with('ZH123456', '测试组合', True)

    def test_update_xueqiu_cube_success(self, client):
        cube_data = {'cube_name': '更新后的组合', 'enabled': False}

        with patch('repositories.xueqiu_repository.XueqiuCubeRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            response = client.put('/api/admin/xueqiu-cubes/ZH123456', json=cube_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '更新成功'
        mock_update.assert_called_once_with('ZH123456', '更新后的组合', False)

    def test_delete_xueqiu_cube_success(self, client):
        with patch('repositories.xueqiu_repository.XueqiuCubeRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            response = client.delete('/api/admin/xueqiu-cubes/ZH123456')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '删除成功'
        mock_delete.assert_called_once_with('ZH123456')

    def test_toggle_xueqiu_cube_success(self, client):
        with patch('repositories.xueqiu_repository.XueqiuCubeRepository.toggle_enabled', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = True
            response = client.post('/api/admin/xueqiu-cubes/ZH123456/toggle', json={'enabled': True})

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['message'] == '操作成功'
        mock_toggle.assert_called_once_with('ZH123456', True)
