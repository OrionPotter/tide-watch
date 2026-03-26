import os
from contextlib import asynccontextmanager, contextmanager

import asyncpg
from asyncpg import PostgresError

from utils.logger import get_logger

logger = get_logger('db')

PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DATABASE = os.getenv('PG_DATABASE', 'tidewatch')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'tidewatch990')
PG_MIN_CONN = int(os.getenv('PG_MIN_CONN', '5'))
PG_MAX_CONN = int(os.getenv('PG_MAX_CONN', '50'))

_pool = None


class DatabaseUnavailableError(RuntimeError):
    """Raised when PostgreSQL is unavailable for the current request."""


async def init_db_pool():
    """Initialize the async PostgreSQL pool."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD,
                min_size=PG_MIN_CONN,
                max_size=PG_MAX_CONN,
                command_timeout=60,
            )
            logger.info(f"Database pool initialized, min={PG_MIN_CONN}, max={PG_MAX_CONN}")
        except (OSError, PostgresError) as exc:
            _pool = None
            logger.warning(f"Database unavailable during pool init: {exc}")
            raise DatabaseUnavailableError("Database is unavailable") from exc


async def close_db_pool():
    """Close the async PostgreSQL pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def get_pool():
    """Return the async PostgreSQL pool."""
    global _pool
    if _pool is None:
        await init_db_pool()
    return _pool


@asynccontextmanager
async def get_db_conn():
    """Acquire and release an async PostgreSQL connection."""
    pool = await get_pool()
    if pool is None:
        raise DatabaseUnavailableError("Database is unavailable")

    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)


def get_db_conn_sync():
    """Return a synchronous PostgreSQL connection for legacy code paths."""
    from psycopg2 import connect
    from psycopg2.extras import RealDictCursor

    return connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
        cursor_factory=RealDictCursor,
    )


@contextmanager
def get_db_conn_context():
    """Acquire and release a synchronous PostgreSQL connection."""
    conn = get_db_conn_sync()
    try:
        yield conn
    finally:
        conn.close()
