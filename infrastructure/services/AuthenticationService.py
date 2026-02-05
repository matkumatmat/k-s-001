from __future__ import annotations
import logging
from uuid import uuid4, UUID
from datetime import datetime, UTC
from typing import TYPE_CHECKING
from domain.client.UserProfileDomain import UserDomain
from domain.management.ValueObject import AuthenticationProvider, AuthenticationOtpPurpose
from infrastructure.services.PasswordService import PasswordService

if TYPE_CHECKING:
    from infrastructure.services.SessionStorageService import SessionStorageService
    from infrastructure.services.OtpService import OtpService
    from domain.client.UserMetadataDomain import UserMetadataDomain
    from fastapi import BackgroundTasks
    from domain.management.OtpAuthenticationDomain import ManagementOtpDomain
    from domain.client.UserSessionDomain import UserSessionDomain

logger = logging.getLogger(__name__)

class AuthenticationService:
    def __init__(
        self,
        uow_factory: callable,
        otp_service: OtpService,
        session_service: SessionStorageService
    ):
        self.uow_factory = uow_factory
        self.otp_service = otp_service
        self.session_service = session_service

    async def register_user(
        self,
        username: str,
        password: str,
        delivery_method: AuthenticationProvider,
        delivery_target: str,
        merchant_id: UUID,
        metadata_info: dict,
        background_tasks: BackgroundTasks,
        email: str | None = None,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None
    ) -> ManagementOtpDomain:

        # Check if user exists
        async with await self.uow_factory() as uow:
            existing_user = await uow.users.get_by_username(username)
            if existing_user:
                raise ValueError("Username already exists")

            if email:
                existing_email = await uow.users.get_by_email(email)
                if existing_email:
                    raise ValueError("Email already exists")

            # Create User Domain
            hashed_password = PasswordService.hash_password(password)
            user_id = uuid4()

            user = UserDomain(
                sid=user_id,
                username=username,
                email=email if email else "", # Handle optional email logic in domain? Domain expects str.
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                metadata=metadata_info,
                primary_contact=delivery_method,
                active=False,
                verified=False
            )

            await uow.users.create(user)
            await uow.commit()

        # Send OTP
        otp = await self.otp_service.createOtp(
            delivery_target=delivery_target,
            delivery_method=delivery_method,
            purpose=AuthenticationOtpPurpose.REGISTRATION,
            merchant_id=merchant_id,
            background_tasks=background_tasks,
            user_id=user_id,
            identifier=username
        )

        return otp

    async def verify_registration(
        self,
        otp_code: str,
        delivery_target: str,
        metadata: UserMetadataDomain,
        background_tasks: BackgroundTasks
    ) -> UserSessionDomain | None:

        otp = await self.otp_service.verifyOtp(
            otp_code=otp_code,
            delivery_target=delivery_target,
            background_tasks=background_tasks
        )

        if not otp or not otp.user_id:
            return None

        if otp.purpose != AuthenticationOtpPurpose.REGISTRATION:
            return None

        async with await self.uow_factory() as uow:
            user = await uow.users.get_by_id(otp.user_id)
            if not user:
                return None

            # Activate User
            now = datetime.now(UTC)
            user.mark_verified(now)
            user.mark_active(now)

            await uow.users.update(user)
            await uow.commit()

        # Create Session
        session = await self.session_service.create_session(
            user_id=otp.user_id,
            metadata=metadata,
            background_tasks=background_tasks
        )

        return session

    async def login(
        self,
        identifier: str,
        password: str,
        metadata: UserMetadataDomain,
        background_tasks: BackgroundTasks
    ) -> UserSessionDomain | None:

        async with await self.uow_factory() as uow:
            # Try by username
            user = await uow.users.get_by_username(identifier)
            if not user:
                # Try by email
                user = await uow.users.get_by_email(identifier)

            if not user:
                return None

            if not PasswordService.verify_password(password, user.password):
                return None

            if not user.can_authenticate():
                return None

        session = await self.session_service.create_session(
            user_id=user.sid,
            metadata=metadata,
            background_tasks=background_tasks
        )

        return session

    async def login_by_token(
        self,
        access_token: str,
        metadata: UserMetadataDomain
    ) -> UserSessionDomain | None:
        return await self.session_service.validate_session(
            active_token=access_token,
            incoming_metadata=metadata
        )
