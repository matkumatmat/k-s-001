from __future__ import annotations
import logging
from uuid import uuid4, UUID
from datetime import datetime, UTC
from typing import TYPE_CHECKING
from domain.client.UserProfileDomain import UserDomain
from domain.management.ValueObject import AuthenticationProvider, AuthenticationOtpPurpose
from infrastructure.services.PasswordService import PasswordService
from domain.logging.LogFactory import LogFactory

if TYPE_CHECKING:
    from infrastructure.services.SessionStorageService import SessionStorageService
    from infrastructure.services.OtpService import OtpService
    from infrastructure.persistence.redis.RedisLogRepository import RedisLogRepository
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
        session_service: SessionStorageService,
        log_repo: RedisLogRepository
    ):
        self.uow_factory = uow_factory
        self.otp_service = otp_service
        self.session_service = session_service
        self.log_repo = log_repo

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

        user_id = None
        try:
            # Check if user exists
            async with await self.uow_factory() as uow:
                existing_user = await uow.users.get_by_username(username)
                if existing_user:
                    # Log registration failure - username exists
                    try:
                        log = LogFactory.create_system_log(
                            action="USER_REGISTRATION_FAILED",
                            message=f"Registration failed: username '{username}' already exists",
                            metadata={
                                "username": username,
                                "reason": "username_exists",
                                "delivery_target": delivery_target
                            }
                        )
                        await self.log_repo.push(log)
                    except Exception as e:
                        logger.warning(f"Failed to log registration failure: {e}")
                    raise ValueError("Username already exists")

                if email:
                    existing_email = await uow.users.get_by_email(email)
                    if existing_email:
                        # Log registration failure - email exists
                        try:
                            log = LogFactory.create_system_log(
                                action="USER_REGISTRATION_FAILED",
                                message=f"Registration failed: email '{email}' already exists",
                                metadata={
                                    "username": username,
                                    "email": email,
                                    "reason": "email_exists",
                                    "delivery_target": delivery_target
                                }
                            )
                            await self.log_repo.push(log)
                        except Exception as e:
                            logger.warning(f"Failed to log registration failure: {e}")
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

            # Log successful registration start
            try:
                log = LogFactory.create_user_behavior_log(
                    user_id=user_id,
                    action="USER_REGISTRATION_STARTED",
                    message=f"User registration started for username '{username}'",
                    metadata={
                        "user_id": str(user_id),
                        "username": username,
                        "email": email,
                        "delivery_target": delivery_target,
                        "delivery_method": delivery_method.value
                    }
                )
                await self.log_repo.push(log)
            except Exception as e:
                logger.warning(f"Failed to log registration start: {e}")

            return otp

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            # Log unexpected registration failure
            try:
                log = LogFactory.create_system_log(
                    action="USER_REGISTRATION_FAILED",
                    message=f"Registration failed with exception: {str(e)}",
                    metadata={
                        "username": username,
                        "reason": "exception",
                        "error": str(e),
                        "user_id": str(user_id) if user_id else None
                    }
                )
                await self.log_repo.push(log)
            except Exception as log_error:
                logger.warning(f"Failed to log registration exception: {log_error}")
            raise

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
            # Log verification failure - invalid OTP (already logged in OtpService)
            return None

        if otp.purpose != AuthenticationOtpPurpose.REGISTRATION:
            # Log verification failure - wrong OTP purpose
            try:
                log = LogFactory.create_user_behavior_log(
                    user_id=otp.user_id,
                    action="REGISTRATION_VERIFICATION_FAILED",
                    message=f"Registration verification failed: wrong OTP purpose",
                    metadata={
                        "user_id": str(otp.user_id),
                        "delivery_target": delivery_target,
                        "reason": "wrong_purpose",
                        "expected": AuthenticationOtpPurpose.REGISTRATION.value,
                        "actual": otp.purpose.value
                    }
                )
                await self.log_repo.push(log)
            except Exception as e:
                logger.warning(f"Failed to log verification failure: {e}")
            return None

        async with await self.uow_factory() as uow:
            user = await uow.users.get_by_id(otp.user_id)
            if not user:
                # Log verification failure - user not found
                try:
                    log = LogFactory.create_user_behavior_log(
                        user_id=otp.user_id,
                        action="REGISTRATION_VERIFICATION_FAILED",
                        message=f"Registration verification failed: user not found",
                        metadata={
                            "user_id": str(otp.user_id),
                            "delivery_target": delivery_target,
                            "reason": "user_not_found"
                        }
                    )
                    await self.log_repo.push(log)
                except Exception as e:
                    logger.warning(f"Failed to log verification failure: {e}")
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

        # Log successful registration verification
        try:
            log = LogFactory.create_user_behavior_log(
                user_id=otp.user_id,
                action="REGISTRATION_VERIFIED",
                message=f"Registration verified successfully for user {otp.user_id}",
                metadata={
                    "user_id": str(otp.user_id),
                    "delivery_target": delivery_target,
                    "session_id": str(session.sid)
                }
            )
            await self.log_repo.push(log)
        except Exception as e:
            logger.warning(f"Failed to log verification success: {e}")

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
                # Log login failure - user not found
                try:
                    log = LogFactory.create_system_log(
                        action="LOGIN_FAILED",
                        message=f"Login failed: user not found for identifier '{identifier}'",
                        metadata={
                            "identifier": identifier,
                            "reason": "user_not_found",
                            "ip_address": metadata.ip_address,
                            "device_type": metadata.device_type.value
                        }
                    )
                    await self.log_repo.push(log)
                except Exception as e:
                    logger.warning(f"Failed to log login failure: {e}")
                return None

            if not PasswordService.verify_password(password, user.password):
                # Log login failure - wrong password
                try:
                    log = LogFactory.create_user_behavior_log(
                        user_id=user.sid,
                        action="LOGIN_FAILED",
                        message=f"Login failed: invalid password for user '{identifier}'",
                        metadata={
                            "user_id": str(user.sid),
                            "identifier": identifier,
                            "reason": "invalid_password",
                            "ip_address": metadata.ip_address,
                            "device_type": metadata.device_type.value
                        }
                    )
                    await self.log_repo.push(log)
                except Exception as e:
                    logger.warning(f"Failed to log login failure: {e}")
                return None

            if not user.can_authenticate():
                # Log login failure - user cannot authenticate (inactive/not verified)
                reason = "not_verified" if not user.verified else "not_active"
                try:
                    log = LogFactory.create_user_behavior_log(
                        user_id=user.sid,
                        action="LOGIN_FAILED",
                        message=f"Login failed: user {reason} for '{identifier}'",
                        metadata={
                            "user_id": str(user.sid),
                            "identifier": identifier,
                            "reason": reason,
                            "verified": user.verified,
                            "active": user.active,
                            "ip_address": metadata.ip_address,
                            "device_type": metadata.device_type.value
                        }
                    )
                    await self.log_repo.push(log)
                except Exception as e:
                    logger.warning(f"Failed to log login failure: {e}")
                return None

        session = await self.session_service.create_session(
            user_id=user.sid,
            metadata=metadata,
            background_tasks=background_tasks
        )

        # Log successful login
        try:
            log = LogFactory.create_user_behavior_log(
                user_id=user.sid,
                action="LOGIN_SUCCESS",
                message=f"User '{identifier}' logged in successfully",
                metadata={
                    "user_id": str(user.sid),
                    "identifier": identifier,
                    "session_id": str(session.sid),
                    "ip_address": metadata.ip_address,
                    "device_type": metadata.device_type.value,
                    "region": metadata.region
                }
            )
            await self.log_repo.push(log)
        except Exception as e:
            logger.warning(f"Failed to log login success: {e}")

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
