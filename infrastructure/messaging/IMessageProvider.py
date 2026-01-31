from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.management.ValueObject import AuthenticationProvider


class IMessageProvider(ABC):

    @abstractmethod
    async def sendOtp(
        self,
        delivery_target: str,
        otp_code: str,
        otp_url: str,
        delivery_method: AuthenticationProvider,
        purpose: str
    ) -> bool:
        pass

    @abstractmethod
    def supportsMethod(self, method: AuthenticationProvider) -> bool:
        pass
