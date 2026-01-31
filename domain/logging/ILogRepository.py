from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.logging.LogEntry import LogEntry

class ILogBufferRepository(ABC):
    """Interface for temporary log storage (Redis)"""

    @abstractmethod
    async def push(self, log: LogEntry) -> None:
        pass

    @abstractmethod
    async def pop_batch(self, batch_size: int) -> List[LogEntry]:
        pass

    @abstractmethod
    async def count(self) -> int:
        pass

class ILogStorageRepository(ABC):
    """Interface for permanent log storage (PostgreSQL)"""

    @abstractmethod
    async def bulk_create(self, logs: List[LogEntry]) -> None:
        pass
