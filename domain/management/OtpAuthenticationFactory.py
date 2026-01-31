from __future__ import annotations
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from domain.management.OtpAuthenticationDomain import ManagementOtpDomain
from domain.management.ValueObject import AuthenticationOtpPurpose, AuthenticationProvider


class OtpAuthenticationFactory:

    @staticmethod
    def generateOtpCode(length: int = 6) -> str:
        code = ''.join([str(secrets.randbelow(10)) for _ in range(length)])
        return code

    @staticmethod
    def createOtp(
        delivery_target: str,
        delivery_method: AuthenticationProvider,
        purpose: AuthenticationOtpPurpose,
        merchant_id: UUID,
        url_prefix: str,
        code_length: int = 6,
        expiry_seconds: int = 300,
        user_id: UUID | None = None,
        identifier: str | None = None
    ) -> ManagementOtpDomain:
        otp_code = OtpAuthenticationFactory.generateOtpCode(code_length)
        otp_url = url_prefix.format(code=otp_code)
        now = datetime.now(timezone.utc)
        expired_at = now + timedelta(seconds=expiry_seconds)

        return ManagementOtpDomain(
            sid=uuid4(),
            otp_code=otp_code,
            otp_url=otp_url,
            delivery_target=delivery_target,
            delivery_method=delivery_method,
            purpose=purpose,
            expired_at=expired_at,
            merchant_id=merchant_id,
            user_id=user_id,
            identifier=identifier,
            expiry_seconds=expiry_seconds,
            code_len=code_length
        )

    @staticmethod
    def createFromPersistence(
        sid: UUID,
        otp_code: str,
        otp_url: str,
        delivery_target: str,
        delivery_method: AuthenticationProvider,
        purpose: AuthenticationOtpPurpose,
        expired_at: datetime,
        merchant_id: UUID,
        used: bool | None,
        used_at: datetime | None,
        created_at: datetime,
        updated_at: datetime,
        user_id: UUID | None,
        identifier: str | None,
        behaviour_logs: UUID | None,
        expiry_seconds: int,
        code_len: int,
        max_retries: int
    ) -> ManagementOtpDomain:
        return ManagementOtpDomain(
            sid=sid,
            otp_code=otp_code,
            otp_url=otp_url,
            delivery_target=delivery_target,
            delivery_method=delivery_method,
            purpose=purpose,
            expired_at=expired_at,
            merchant_id=merchant_id,
            used=used,
            used_at=used_at,
            created_at=created_at,
            updated_at=updated_at,
            user_id=user_id,
            identifier=identifier,
            behaviour_logs=behaviour_logs,
            expiry_seconds=expiry_seconds,
            code_len=code_len,
            max_retries=max_retries
        )
