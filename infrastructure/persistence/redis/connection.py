from __future__ import annotations
import os
from _collections_abc import AsyncGenerator
from redis.asyncio import Redis, ConnectionPool
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))


class RedisConnection:
    _pool: ConnectionPool | None = None

    @classmethod
    def get_pool(cls) -> ConnectionPool:
        if cls._pool is None:
            cls._pool = ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                max_connections=REDIS_MAX_CONNECTIONS,
                decode_responses=True
            )
        return cls._pool

    @classmethod
    async def get_client(cls) -> Redis:
        pool = cls.get_pool()
        return Redis(connection_pool=pool)

    @classmethod
    async def close_pool(cls) -> None:
        if cls._pool is not None:
            await cls._pool.aclose()
            cls._pool = None


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    client = await RedisConnection.get_client()
    try:
        yield client
    finally:
        await client.aclose()
