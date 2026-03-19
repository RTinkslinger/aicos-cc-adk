"""Asyncpg connection pool management for State MCP."""

import asyncio
import os

import asyncpg

_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()


async def get_pool() -> asyncpg.Pool:
    """Get or create the asyncpg connection pool.

    Reads DATABASE_URL from environment. Pool is created lazily on first call
    and reused for subsequent calls. Lock prevents concurrent pool creation.
    """
    global _pool
    async with _pool_lock:
        if _pool is None:
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                raise RuntimeError("DATABASE_URL not set. Check /opt/agents/.env")
            _pool = await asyncpg.create_pool(
                db_url,
                min_size=1,
                max_size=3,
                statement_cache_size=0,
                command_timeout=30,
            )
    return _pool


async def close_pool() -> None:
    """Close the connection pool and reset the global reference."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
