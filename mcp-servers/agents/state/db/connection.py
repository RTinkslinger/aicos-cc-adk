"""Asyncpg connection pool management for State MCP."""

import os

import asyncpg

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the asyncpg connection pool.

    Reads DATABASE_URL from environment. Pool is created lazily on first call
    and reused for subsequent calls.
    """
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            os.environ["DATABASE_URL"],
            min_size=2,
            max_size=5,
        )
    return _pool


async def close_pool() -> None:
    """Close the connection pool and reset the global reference."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
