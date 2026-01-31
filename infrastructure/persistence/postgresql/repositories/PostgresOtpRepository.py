from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.management.IOtpRepository import IOtpRepository
from domain.management.OtpAuthenticationDomain import ManagementOtpDomain
from domain.management.ValueObject import AuthenticationOtpPurpose
from infrastructure.persistence.postgresql.models.OtpModel import OtpModel
from infrastructure.persistence.postgresql.mappers.OtpMapper import OtpMapper


class PostgresOtpRepository(IOtpRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, domain: ManagementOtpDomain) -> ManagementOtpDomain:
        model = OtpMapper.toModel(domain)
        self.session.add(model)
        await self.session.flush()
        return domain

    async def getById(self, sid: UUID) -> ManagementOtpDomain | None:
        stmt = select(OtpModel).where(OtpModel.sid == sid)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return OtpMapper.toDomain(model)

    async def getByCodeAndTarget(self, otp_code: str, delivery_target: str) -> ManagementOtpDomain | None:
        stmt = select(OtpModel).where(
            OtpModel.otp_code == otp_code,
            OtpModel.delivery_target == delivery_target
        ).order_by(OtpModel.created_at.desc())
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return OtpMapper.toDomain(model)

    async def getByTarget(self, delivery_target: str) -> list[ManagementOtpDomain]:
        stmt = select(OtpModel).where(
            OtpModel.delivery_target == delivery_target
        ).order_by(OtpModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [OtpMapper.toDomain(model) for model in models]

    async def getByUserIdAndPurpose(self, user_id: UUID, purpose: AuthenticationOtpPurpose) -> list[ManagementOtpDomain]:
        stmt = select(OtpModel).where(
            OtpModel.user_id == user_id,
            OtpModel.purpose == purpose.value
        ).order_by(OtpModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [OtpMapper.toDomain(model) for model in models]

    async def update(self, domain: ManagementOtpDomain) -> ManagementOtpDomain:
        stmt = select(OtpModel).where(OtpModel.sid == domain.sid)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            raise ValueError(f"OTP {domain.sid} not found")

        OtpMapper.updateModel(model, domain)
        await self.session.flush()
        return domain

    async def delete(self, sid: UUID) -> bool:
        stmt = select(OtpModel).where(OtpModel.sid == sid)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return False

        await self.session.delete(model)
        await self.session.flush()
        return True

    async def exists(self, sid: UUID) -> bool:
        stmt = select(OtpModel.sid).where(OtpModel.sid == sid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
