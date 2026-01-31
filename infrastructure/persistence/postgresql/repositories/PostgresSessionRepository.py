from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from domain.client.ISessionRepository import ISessionRepository
from domain.client.UserSessionDomain import UserSessionDomain
from infrastructure.persistence.postgresql.models.SessionModel import SessionModel
from infrastructure.persistence.postgresql.mappers.SessionMapper import SessionMapper


class PostgresSessionRepository(ISessionRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, domain: UserSessionDomain) -> UserSessionDomain:
        model = SessionMapper.to_model(domain)
        self.session.add(model)
        await self.session.flush()
        return domain

    async def get_by_id(self, sid: UUID) -> UserSessionDomain | None:
        stmt = select(SessionModel).where(
            SessionModel.sid == sid,
            SessionModel.deleted == False
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return SessionMapper.to_domain(model)

    async def get_by_user_id(self, user_id: UUID) -> list[UserSessionDomain]:
        stmt = select(SessionModel).where(
            SessionModel.user_id == user_id,
            SessionModel.deleted == False
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [SessionMapper.to_domain(model) for model in models]

    async def get_by_active_token(self, active_token: str) -> UserSessionDomain | None:
        stmt = select(SessionModel).where(
            SessionModel.active_token == active_token,
            SessionModel.deleted == False
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return SessionMapper.to_domain(model)

    async def get_by_refresh_token(self, refresh_token: str) -> UserSessionDomain | None:
        stmt = select(SessionModel).where(
            SessionModel.refresh_token == refresh_token,
            SessionModel.deleted == False
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return SessionMapper.to_domain(model)

    async def update(self, domain: UserSessionDomain) -> UserSessionDomain:
        stmt = select(SessionModel).where(
            SessionModel.sid == domain.sid,
            SessionModel.deleted == False
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"Session {domain.sid} not found")

        SessionMapper.update_model(model, domain)
        await self.session.flush()
        return domain

    async def delete(self, sid: UUID) -> bool:
        stmt = (
            update(SessionModel)
            .where(SessionModel.sid == sid, SessionModel.deleted == False)
            .values(deleted=True, deleted_at=datetime.now(timezone.utc))
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def delete_all_by_user(self, user_id: UUID) -> int:
        stmt = (
            update(SessionModel)
            .where(SessionModel.user_id == user_id, SessionModel.deleted == False)
            .values(deleted=True, deleted_at=datetime.now(timezone.utc))
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def exists(self, sid: UUID) -> bool:
        stmt = select(SessionModel.sid).where(
            SessionModel.sid == sid,
            SessionModel.deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
