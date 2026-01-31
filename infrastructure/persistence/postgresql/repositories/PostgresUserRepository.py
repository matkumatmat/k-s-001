from __future__ import annotations
from sqlalchemy import select, update, delete
from domain.client.IUserRepository import IUserRepository
from infrastructure.persistence.postgresql.models.UserModel import UserModel
from infrastructure.persistence.postgresql.mappers.UserMapper import UserMapper
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.UserProfileDomain import UserDomain
    from sqlalchemy.ext.asyncio import AsyncSession
    from uuid import UUID

class PostgresUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user: UserDomain) -> None:
        model = UserMapper.to_model(user)
        self._session.add(model)
        # Assuming commit is handled by UoW

    async def get_by_id(self, sid: UUID) -> UserDomain | None:
        result = await self._session.execute(select(UserModel).where(UserModel.sid == sid))
        model = result.scalar_one_or_none()
        if model:
            return UserMapper.to_domain(model)
        return None

    async def get_by_username(self, username: str) -> UserDomain | None:
        result = await self._session.execute(select(UserModel).where(UserModel.username == username))
        model = result.scalar_one_or_none()
        if model:
            return UserMapper.to_domain(model)
        return None

    async def get_by_email(self, email: str) -> UserDomain | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        if model:
            return UserMapper.to_domain(model)
        return None

    async def update(self, user: UserDomain) -> None:
        model = UserMapper.to_model(user)
        query = update(UserModel).where(UserModel.sid == user.sid).values(
            username=model.username,
            email=model.email,
            password=model.password,
            first_name=model.first_name,
            last_name=model.last_name,
            phone=model.phone,
            address=model.address,
            region=model.region,
            register_geolocation=model.register_geolocation,
            metadata_info=model.metadata_info,
            primary_contact=model.primary_contact,
            role=model.role,
            active=model.active,
            actived_at=model.actived_at,
            verified=model.verified,
            verified_at=model.verified_at,
            updated_at=model.updated_at,
            deleted=model.deleted,
            deleted_at=model.deleted_at
        )
        await self._session.execute(query)

    async def delete(self, sid: UUID) -> None:
        query = delete(UserModel).where(UserModel.sid == sid)
        await self._session.execute(query)
