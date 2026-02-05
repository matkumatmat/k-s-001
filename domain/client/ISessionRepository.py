from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.UserSessionDomain import UserSessionDomain
    from uuid import UUID


class ISessionRepository(ABC):

    @abstractmethod
    async def create(self, session: UserSessionDomain) -> UserSessionDomain:
        pass

    @abstractmethod
    async def get_by_id(self, sid: UUID) -> UserSessionDomain | None:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[UserSessionDomain]:
        pass

    @abstractmethod
    async def get_by_active_token(self, active_token: str) -> UserSessionDomain | None:
        pass

    @abstractmethod
    async def get_by_refresh_token(self, refresh_token: str) -> UserSessionDomain | None:
        pass

    @abstractmethod
    async def update(self, session: UserSessionDomain) -> UserSessionDomain:
        pass

    @abstractmethod
    async def delete(self, sid: UUID) -> bool:
        pass

    @abstractmethod
    async def delete_all_by_user(self, user_id: UUID) -> int:
        pass

    @abstractmethod
    async def exists(self, sid: UUID) -> bool:
        pass
