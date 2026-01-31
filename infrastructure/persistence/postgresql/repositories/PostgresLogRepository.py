from __future__ import annotations
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from infrastructure.persistence.postgresql.models.LogModel import LogModel
from domain.logging.ILogRepository import ILogStorageRepository
from domain.logging.LogEntry import LogEntry

class PostgresLogRepository(ILogStorageRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def bulk_create(self, logs: List[LogEntry]) -> None:
        if not logs:
            return

        log_dicts = [
            {
                "id": log.id,
                "log_type": log.log_type.value,
                "action": log.action,
                "message": log.message,
                "metadata_payload": log.metadata,
                "created_at": log.created_at,
                "user_id": log.user_id
            }
            for log in logs
        ]

        # Using SQLAlchemy Core for bulk insert which is faster
        stmt = insert(LogModel).values(log_dicts)
        await self._session.execute(stmt)
