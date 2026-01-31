from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.UserProfileDomain import UserDomain
    from uuid import UUID

class IUserRepository(ABC):
    @abstractmethod
    async def create(self, user: UserDomain) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, sid: UUID) -> UserDomain | None:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> UserDomain | None:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> UserDomain | None:
        pass

    @abstractmethod
    async def update(self, user: UserDomain) -> None:
        pass

    @abstractmethod
    async def delete(self, sid: UUID) -> None:
        pass
