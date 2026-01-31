"""Manual log sync script to test PostgreSQL synchronization"""
import asyncio
import logging
from infrastructure.persistence.redis.connection import RedisConnection
from infrastructure.persistence.postgresql.connection import DatabaseConnection
from infrastructure.persistence.redis.RedisLogRepository import RedisLogRepository
from infrastructure.persistence.uow.PostgresUnitOfWork import PostgresUnitOfWork
from infrastructure.services.LogSyncService import LogSyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def manual_sync():
    logger.info("Starting manual log synchronization...")

    # Initialize dependencies
    redis_client = await RedisConnection.get_client()
    redis_repo = RedisLogRepository(redis_client)

    # Check Redis buffer count
    count_before = await redis_repo.count()
    logger.info(f"Logs in Redis buffer before sync: {count_before}")

    async def uow_factory():
        session_factory = DatabaseConnection.get_session_factory()
        session = session_factory()
        return PostgresUnitOfWork(session)

    service = LogSyncService(redis_repo, uow_factory)
    synced_count = await service.sync_logs()

    logger.info(f"Successfully synced {synced_count} logs to PostgreSQL")

    # Check Redis buffer count after sync
    count_after = await redis_repo.count()
    logger.info(f"Logs remaining in Redis buffer: {count_after}")

    # Close connections
    await RedisConnection.close_pool()
    await DatabaseConnection.close()

    logger.info("Manual log synchronization completed")

if __name__ == "__main__":
    asyncio.run(manual_sync())
