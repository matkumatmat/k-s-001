from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.persistence.uow.IUnitOfWork import IUnitOfWork
from infrastructure.persistence.postgresql.repositories.PostgresSessionRepository import PostgresSessionRepository
from infrastructure.persistence.postgresql.repositories.PostgresOtpRepository import PostgresOtpRepository
from domain.client.ISessionRepository import ISessionRepository
from domain.management.IOtpRepository import IOtpRepository


class PostgresUnitOfWork(IUnitOfWork):

    def __init__(self, session: AsyncSession):
        self._session = session
        self._sessions: ISessionRepository | None = None
        self._otps: IOtpRepository | None = None

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
