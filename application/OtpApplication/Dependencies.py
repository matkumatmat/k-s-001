from __future__ import annotations
from infrastructure.persistence.redis.connection import RedisConnection
from infrastructure.persistence.postgresql.connection import DatabaseConnection
from infrastructure.persistence.redis.RedisOtpRepository import RedisOtpRepository
from infrastructure.persistence.uow.PostgresUnitOfWork import PostgresUnitOfWork
from infrastructure.services.OtpService import OtpService
from infrastructure.messaging.ConsoleMessageProvider import ConsoleMessageProvider


async def getOtpService() -> OtpService:
    redis = await RedisConnection.get_client()
    redis_repo = RedisOtpRepository(redis)

    async def uow_factory():
        db_session = DatabaseConnection.get_session_factory()()
        return PostgresUnitOfWork(db_session)

    message_provider = ConsoleMessageProvider()

    return OtpService(
        redis_repo=redis_repo,
        uow_factory=uow_factory,
        message_provider=message_provider
    )
