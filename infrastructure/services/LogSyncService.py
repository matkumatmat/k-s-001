from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    from infrastructure.persistence.redis.RedisLogRepository import RedisLogRepository
    from infrastructure.persistence.uow.PostgresUnitOfWork import PostgresUnitOfWork

logger = logging.getLogger(__name__)

class LogSyncService:
    def __init__(
        self,
        redis_repo: RedisLogRepository,
        uow_factory: Callable[[], Awaitable[PostgresUnitOfWork]]
    ):
        self.redis_repo = redis_repo
        self.uow_factory = uow_factory

    async def sync_logs(self, batch_size: int = 1000) -> int:
        """
        Synchronizes logs from Redis buffer to PostgreSQL storage.

        Args:
            batch_size: Maximum number of logs to process in one transaction.

        Returns:
            Total number of logs synchronized.
        """
        total_synced = 0
        try:
            while True:
                # 1. Pop batch from Redis
                logs = await self.redis_repo.pop_batch(batch_size)
                if not logs:
                    break

                # 2. Save to PostgreSQL
                try:
                    async with await self.uow_factory() as uow:
                        await uow.logs.bulk_create(logs)
                        await uow.commit()

                    total_synced += len(logs)
                    logger.info(f"Synced {len(logs)} logs to PostgreSQL")

                except Exception as e:
                    logger.error(f"Failed to save logs to database: {e}")
                    # In a production system, we should re-queue these logs to Redis
                    # or move them to a Dead Letter Queue (DLQ).
                    # For now, we log the error. The logs are lost from Redis (popped).
                    # We continue to try next batch or stop?
                    # Stopping is safer to avoid losing more data if DB is down.
                    break

                # If we retrieved fewer items than batch_size, queue is likely empty
                if len(logs) < batch_size:
                    break

        except Exception as e:
            logger.error(f"Critical error during log synchronization: {e}")

        return total_synced
