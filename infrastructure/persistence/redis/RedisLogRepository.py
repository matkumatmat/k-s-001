from __future__ import annotations
import json
from uuid import UUID
from datetime import datetime
from typing import List, TYPE_CHECKING
from domain.logging.ILogRepository import ILogBufferRepository
from domain.logging.LogEntry import LogEntry
from domain.logging.LogType import LogType

if TYPE_CHECKING:
    from redis.asyncio import Redis

class RedisLogRepository(ILogBufferRepository):
    KEY = "system:logs:buffer"

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def _serialize(self, log: LogEntry) -> str:
        return json.dumps(log.to_dict())

    def _deserialize(self, data: str) -> LogEntry:
        obj = json.loads(data)
        return LogEntry(
            id=UUID(obj["id"]),
            log_type=LogType(obj["log_type"]),
            action=obj["action"],
            message=obj["message"],
            metadata=obj["metadata"],
            created_at=datetime.fromisoformat(obj["created_at"]),
            user_id=UUID(obj["user_id"]) if obj["user_id"] else None
        )

    async def push(self, log: LogEntry) -> None:
        data = self._serialize(log)
        await self.redis.lpush(self.KEY, data)

    async def pop_batch(self, batch_size: int) -> List[LogEntry]:
        # Redis RPOP with count is available in newer redis versions
        # Using pipeline for atomicity if needed, but RPOP count is atomic
        # However, to avoid data loss if crash happens during processing,
        # usually we might want LMOVE or similar.
        # But per requirements: "store in redis, then append to DB, clean redis".
        # Simplest approach: RPOP count. If DB insert fails, we lose logs?
        # User said "store in redis, then at interval append to db, clean cache".
        # Safe approach: LRange -> Insert DB -> LTrim.

        # Let's use LRANGE + LTRIM approach to ensure we only remove what we read.
        # But since others might be pushing to LPUSH (left), we should read from right (R).
        # List: [Newest ... Oldest] (if LPUSH)
        # So we want to take from Right (Oldest).
        # LRANGE -batch_size -1 gives last N items.
        # But LTRIM keeps range.

        # Alternative: RPOP batch_size (removes and returns).
        # If crash, logs lost.
        # Better: LMOVE to a processing list?
        # Given "clean cache in redis" instruction, RPOP seems acceptable for log data (often best effort).
        # But `lpop` (or `rpop`) takes `count` argument in redis 6.2+.

        # I'll use `rpop(key, count)`.

        raw_items = await self.redis.rpop(self.KEY, count=batch_size)
        if not raw_items:
            return []

        return [self._deserialize(item) for item in raw_items]

    async def count(self) -> int:
        return await self.redis.llen(self.KEY)
