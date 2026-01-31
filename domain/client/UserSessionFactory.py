from __future__ import annotations
from datetime import datetime, timedelta, UTC
from uuid import UUID, uuid4
from domain.client.UserSessionDomain import UserSessionDomain
from domain.client.DeviceFingerprintVO import DeviceFingerprintVO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.UserMetadataDomain import UserMetadataDomain


class UserSessionFactory:

    @staticmethod
    def create_new_session(
        user_id: UUID,
        metadata: UserMetadataDomain,
        session_duration_days: int = 30
    ) -> UserSessionDomain:
        now = datetime.now(UTC)
        expiry = now + timedelta(days=session_duration_days)
        fingerprint = DeviceFingerprintVO.from_metadata(metadata)

        return UserSessionDomain(
            sid=uuid4(),
            user_id=user_id,
            active=now,
            expiry=expiry,
            metadata=metadata,
            device_fingerprint=fingerprint
        )

    @staticmethod
    def create_from_persistence(
        sid: UUID,
        user_id: UUID,
        active: datetime,
        expiry: datetime,
        metadata: UserMetadataDomain,
        device_fingerprint: DeviceFingerprintVO,
        active_token: str,
        refresh_token: str
    ) -> UserSessionDomain:
        session = UserSessionDomain(
            sid=sid,
            user_id=user_id,
            active=active,
            expiry=expiry,
            metadata=metadata,
            device_fingerprint=device_fingerprint
        )
        session.active_token = active_token
        session.refresh_token = refresh_token
        return session

    @staticmethod
    def create_with_custom_expiry(
        user_id: UUID,
        metadata: UserMetadataDomain,
        expiry_duration: timedelta
    ) -> UserSessionDomain:
        now = datetime.now(UTC)
        expiry = now + expiry_duration
        fingerprint = DeviceFingerprintVO.from_metadata(metadata)

        return UserSessionDomain(
            sid=uuid4(),
            user_id=user_id,
            active=now,
            expiry=expiry,
            metadata=metadata,
            device_fingerprint=fingerprint
        )
