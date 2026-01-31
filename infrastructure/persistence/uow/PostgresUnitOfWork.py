from __future__ import annotations
from infrastructure.persistence.uow.IUnitOfWork import IUnitOfWork
from infrastructure.persistence.postgresql.repositories.PostgresSessionRepository import PostgresSessionRepository
from infrastructure.persistence.postgresql.repositories.PostgresOtpRepository import PostgresOtpRepository
from infrastructure.persistence.postgresql.repositories.PostgresUserRepository import PostgresUserRepository
from infrastructure.persistence.postgresql.repositories.PostgresLogRepository import PostgresLogRepository
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.IUserRepository import IUserRepository
    from domain.management.IOtpRepository import IOtpRepository
    from domain.client.ISessionRepository import ISessionRepository
    from domain.logging.ILogRepository import ILogStorageRepository
    from sqlalchemy.ext.asyncio import AsyncSession


class PostgresUnitOfWork(IUnitOfWork):

    def __init__(self, session: AsyncSession):
        self._session = session
        self._sessions: ISessionRepository | None = None
        self._otps: IOtpRepository | None = None
        self._users: IUserRepository | None = None
        self._logs: ILogStorageRepository | None = None

    @property
    def sessions(self) -> ISessionRepository:
        if self._sessions is None:
            self._sessions = PostgresSessionRepository(self._session)
        return self._sessions

    @property
    def otps(self) -> IOtpRepository:
        if self._otps is None:
            self._otps = PostgresOtpRepository(self._session)
        return self._otps

    @property
    def users(self) -> IUserRepository:
        if self._users is None:
            self._users = PostgresUserRepository(self._session)
        return self._users

    @property
    def logs(self) -> ILogStorageRepository:
        if self._logs is None:
            self._logs = PostgresLogRepository(self._session)
        return self._logs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
