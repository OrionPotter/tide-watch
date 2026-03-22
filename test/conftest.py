import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_conn():
    mock_conn = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=None)
    return mock_conn


@pytest.fixture
def client(mock_db_conn):
    with patch('utils.db.init_db_pool', new_callable=AsyncMock), \
         patch('utils.db.close_db_pool', new_callable=AsyncMock), \
         patch('utils.db.get_db_conn', return_value=mock_db_conn):
        app = FastAPI()
        from api.router_registry import register_api_routers

        register_api_routers(app)
        with TestClient(app) as test_client:
            yield test_client
