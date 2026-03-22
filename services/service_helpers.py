import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar('T')


def clear_proxy_env() -> None:
    for key in ('http_proxy', 'https_proxy', 'all_proxy'):
        os.environ.pop(key, None)


def build_xueqiu_headers() -> dict[str, str]:
    token = os.getenv('AKSHARE_TOKEN', '')
    return {
        'Cookie': f'xq_a_token={token};',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://xueqiu.com/',
    }


def run_async(coro_factory: Callable[[], Awaitable[T]]) -> T:
    return asyncio.run(coro_factory())


def success_or_failure(success: bool, success_message: str, failure_message: str) -> tuple[bool, str]:
    return success, success_message if success else failure_message
