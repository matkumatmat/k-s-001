from __future__ import annotations
from typing import AsyncGenerator
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.persistence.redis.connection import get_redis_client, RedisConnection
from infrastructure.persistence.postgresql.connection import get_db_session, DatabaseConnection
from infrastructure.persistence.redis.RedisSessionRepository import RedisSessionRepository
from infrastructure.persistence.uow.PostgresUnitOfWork import PostgresUnitOfWork
from infrastructure.services.SessionStorageService import SessionStorageService


async def getRedisClient() -> AsyncGenerator[Redis, None]:
    client = await RedisConnection.get_client()
    try:
        yield client
    finally:
        await client.aclose()


async def getDbSession() -> AsyncGenerator[AsyncSession, None]:
    factory = DatabaseConnection.get_session_factory()
    async with factory() as session:
        yield session


async def getRedisRepository(redis: Redis = None) -> RedisSessionRepository:
    if redis is None:
        redis = await RedisConnection.get_client()
    return RedisSessionRepository(redis)


def getUowFactory(session: AsyncSession):
    async def factory():
        return PostgresUnitOfWork(session)
    return factory


async def getSessionStorageService() -> SessionStorageService:
    redis = await RedisConnection.get_client()
    redis_repo = RedisSessionRepository(redis)

    async def uow_factory():
        db_session = DatabaseConnection.get_session_factory()()
        return PostgresUnitOfWork(db_session)

    return SessionStorageService(
        redis_repo=redis_repo,
        uow_factory=uow_factory
    )
