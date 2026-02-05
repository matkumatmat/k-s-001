from __future__ import annotations
import logging
from infrastructure.messaging.IMessageProvider import IMessageProvider
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.management.ValueObject import AuthenticationProvider

logger = logging.getLogger(__name__)


class ConsoleMessageProvider(IMessageProvider):

    async def sendOtp(
        self,
        delivery_target: str,
        otp_code: str,
        otp_url: str,
        delivery_method: AuthenticationProvider,
        purpose: str
    ) -> bool:
        logger.info("=" * 80)
        logger.info("OTP SENT (Console Provider - Development Only)")
        logger.info("=" * 80)
        logger.info(f"Target: {delivery_target}")
        logger.info(f"Method: {delivery_method.value}")
        logger.info(f"Purpose: {purpose}")
        logger.info(f"OTP Code: {otp_code}")
        logger.info(f"OTP URL: {otp_url}")
        logger.info("=" * 80)

        print("\n" + "=" * 80)
        print("🔐 OTP NOTIFICATION (Development Mode)")
        print("=" * 80)
        print(f"📧 Target: {delivery_target}")
        print(f"📱 Method: {delivery_method.value.upper()}")
        print(f"🎯 Purpose: {purpose.upper()}")
        print(f"🔢 Code: {otp_code}")
        print(f"🔗 Link: {otp_url}")
        print("=" * 80 + "\n")

        return True

    def supportsMethod(self, method: AuthenticationProvider) -> bool:
        return True
