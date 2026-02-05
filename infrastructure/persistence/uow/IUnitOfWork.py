from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.ISessionRepository import ISessionRepository
    from domain.management.IOtpRepository import IOtpRepository
    from domain.client.IUserRepository import IUserRepository


class IUnitOfWork(ABC):

    @property
    @abstractmethod
    def sessions(self) -> ISessionRepository:
        pass

    @property
    @abstractmethod
    def otps(self) -> IOtpRepository:
        pass

    @property
    @abstractmethod
    def users(self) -> IUserRepository:
        pass

    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass
