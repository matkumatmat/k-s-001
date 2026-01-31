from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import UUID
from domain.management.OtpAuthenticationDomain import ManagementOtpDomain
from domain.management.ValueObject import AuthenticationOtpPurpose


class IOtpRepository(ABC):

    @abstractmethod
    async def create(self, otp: ManagementOtpDomain) -> ManagementOtpDomain:
        pass

    @abstractmethod
    async def getById(self, sid: UUID) -> ManagementOtpDomain | None:
        pass

    @abstractmethod
    async def getByCodeAndTarget(self, otp_code: str, delivery_target: str) -> ManagementOtpDomain | None:
        pass

    @abstractmethod
    async def getByTarget(self, delivery_target: str) -> list[ManagementOtpDomain]:
        pass

    @abstractmethod
    async def getByUserIdAndPurpose(self, user_id: UUID, purpose: AuthenticationOtpPurpose) -> list[ManagementOtpDomain]:
        pass

    @abstractmethod
    async def update(self, otp: ManagementOtpDomain) -> ManagementOtpDomain:
        pass

    @abstractmethod
    async def delete(self, sid: UUID) -> bool:
        pass

    @abstractmethod
    async def exists(self, sid: UUID) -> bool:
        pass
