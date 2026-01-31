from __future__ import annotations
import logging
import os
from datetime import datetime, UTC
from typing import TYPE_CHECKING
from domain.management.OtpAuthenticationFactory import OtpAuthenticationFactory
from domain.logging.LogFactory import LogFactory

if TYPE_CHECKING:
    from domain.management.OtpAuthenticationDomain import ManagementOtpDomain
    from infrastructure.messaging.IMessageProvider import IMessageProvider
    from infrastructure.persistence.redis.RedisOtpRepository import RedisOtpRepository
    from infrastructure.persistence.redis.RedisLogRepository import RedisLogRepository
    from domain.management.ValueObject import AuthenticationOtpPurpose, AuthenticationProvider
    from uuid import UUID
    from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


class OtpService:

    def __init__(
        self,
        redis_repo: RedisOtpRepository,
        uow_factory: callable,
        message_provider: IMessageProvider,
        log_repo: RedisLogRepository
    ):
        self.redis_repo = redis_repo
        self.uow_factory = uow_factory
        self.message_provider = message_provider
        self.log_repo = log_repo
        self.url_prefix = os.getenv("OTP_URL_PREFIX", "http://localhost:8000/auth/verify?code={code}")
        self.code_length = int(os.getenv("OTP_CODE_LEN", "6"))
        self.expiry_seconds = int(os.getenv("OTP_EXPIRES_SECONDS", "300"))
        self.max_retries = int(os.getenv("OTP_MAX_RETRIES", "3"))

    async def createOtp(
        self,
        delivery_target: str,
        delivery_method: AuthenticationProvider,
        purpose: AuthenticationOtpPurpose,
        merchant_id: UUID,
        background_tasks: BackgroundTasks,
        user_id: UUID | None = None,
        identifier: str | None = None
    ) -> ManagementOtpDomain:
        otp = OtpAuthenticationFactory.createOtp(
            delivery_target=delivery_target,
            delivery_method=delivery_method,
            purpose=purpose,
            merchant_id=merchant_id,
            url_prefix=self.url_prefix,
            code_length=self.code_length,
            expiry_seconds=self.expiry_seconds,
            user_id=user_id,
            identifier=identifier
        )

        await self.redis_repo.create(otp)

        background_tasks.add_task(
            self._syncToPostgres,
            otp,
            operation="create"
        )

        background_tasks.add_task(
            self._sendOtpMessage,
            otp
        )

        # Log OTP creation
        try:
            log = LogFactory.create_system_log(
                action="OTP_CREATED",
                message=f"OTP created for {delivery_target} via {delivery_method.value}",
                metadata={
                    "otp_id": str(otp.sid),
                    "delivery_target": delivery_target,
                    "delivery_method": delivery_method.value,
                    "purpose": purpose.value,
                    "expires_at": otp.expired_at.isoformat(),
                    "user_id": str(user_id) if user_id else None
                }
            )
            await self.log_repo.push(log)
        except Exception as e:
            logger.warning(f"Failed to log OTP creation: {e}")

        return otp

    async def verifyOtp(
        self,
        otp_code: str,
        delivery_target: str,
        background_tasks: BackgroundTasks
    ) -> ManagementOtpDomain | None:
        otp = await self.redis_repo.getByCodeAndTarget(otp_code, delivery_target)

        if otp is None:
            async with await self.uow_factory() as uow:
                otp = await uow.otps.getByCodeAndTarget(otp_code, delivery_target)

        if otp is None:
            # Log verification failure - OTP not found (SYSTEM log since no user context)
            try:
                log = LogFactory.create_system_log(
                    action="OTP_VERIFICATION_FAILED",
                    message=f"OTP verification failed: code not found for {delivery_target}",
                    metadata={
                        "delivery_target": delivery_target,
                        "reason": "otp_not_found"
                    }
                )
                await self.log_repo.push(log)
            except Exception as e:
                logger.warning(f"Failed to log OTP verification failure: {e}")
            return None

        current_time = datetime.now(UTC)

        if otp.is_expired(current_time):
            # Log verification failure - OTP expired
            try:
                log = LogFactory.create_user_behavior_log(
                    user_id=otp.user_id,
                    action="OTP_VERIFICATION_FAILED",
                    message=f"OTP verification failed: code expired for {delivery_target}",
                    metadata={
                        "otp_id": str(otp.sid),
                        "delivery_target": delivery_target,
                        "reason": "expired",
                        "expired_at": otp.expired_at.isoformat()
                    }
                )
                await self.log_repo.push(log)
            except Exception as e:
                logger.warning(f"Failed to log OTP verification failure: {e}")
            return None

        if otp.used:
            # Log verification failure - OTP already used
            try:
                log = LogFactory.create_user_behavior_log(
                    user_id=otp.user_id,
                    action="OTP_VERIFICATION_FAILED",
                    message=f"OTP verification failed: code already used for {delivery_target}",
                    metadata={
                        "otp_id": str(otp.sid),
                        "delivery_target": delivery_target,
                        "reason": "already_used",
                        "used_at": otp.used_at.isoformat() if otp.used_at else None
                    }
                )
                await self.log_repo.push(log)
            except Exception as e:
                logger.warning(f"Failed to log OTP verification failure: {e}")
            return None

        otp.mark_used(current_time)

        await self.redis_repo.update(otp)

        background_tasks.add_task(
            self._syncToPostgres,
            otp,
            operation="update"
        )

        # Log successful verification
        try:
            log = LogFactory.create_user_behavior_log(
                user_id=otp.user_id,
                action="OTP_VERIFIED",
                message=f"OTP verified successfully for {delivery_target}",
                metadata={
                    "otp_id": str(otp.sid),
                    "delivery_target": delivery_target,
                    "purpose": otp.purpose.value,
                    "delivery_method": otp.delivery_method.value
                }
            )
            await self.log_repo.push(log)
        except Exception as e:
            logger.warning(f"Failed to log OTP verification success: {e}")

        return otp

    async def getOtpById(self, sid: UUID) -> ManagementOtpDomain | None:
        otp = await self.redis_repo.getById(sid)
        if otp:
            return otp

        async with await self.uow_factory() as uow:
            return await uow.otps.getById(sid)

    async def _sendOtpMessage(self, otp: ManagementOtpDomain) -> None:
        try:
            success = await self.message_provider.sendOtp(
                delivery_target=otp.delivery_target,
                otp_code=otp.otp_code,
                otp_url=otp.otp_url,
                delivery_method=otp.delivery_method,
                purpose=otp.purpose.value
            )
            if success:
                logger.info(f"OTP sent successfully to {otp.delivery_target} via {otp.delivery_method.value}")
                # Log successful send
                try:
                    log = LogFactory.create_system_log(
                        action="OTP_SENT",
                        message=f"OTP sent successfully to {otp.delivery_target} via {otp.delivery_method.value}",
                        metadata={
                            "otp_id": str(otp.sid),
                            "delivery_target": otp.delivery_target,
                            "delivery_method": otp.delivery_method.value,
                            "purpose": otp.purpose.value
                        }
                    )
                    await self.log_repo.push(log)
                except Exception as e:
                    logger.warning(f"Failed to log OTP send success: {e}")
            else:
                logger.error(f"Failed to send OTP to {otp.delivery_target}")
                # Log send failure
                try:
                    log = LogFactory.create_system_log(
                        action="OTP_SEND_FAILED",
                        message=f"Failed to send OTP to {otp.delivery_target}",
                        metadata={
                            "otp_id": str(otp.sid),
                            "delivery_target": otp.delivery_target,
                            "delivery_method": otp.delivery_method.value,
                            "reason": "message_provider_failed"
                        }
                    )
                    await self.log_repo.push(log)
                except Exception as e:
                    logger.warning(f"Failed to log OTP send failure: {e}")
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            # Log send error
            try:
                log = LogFactory.create_system_log(
                    action="OTP_SEND_FAILED",
                    message=f"Error sending OTP to {otp.delivery_target}: {str(e)}",
                    metadata={
                        "otp_id": str(otp.sid),
                        "delivery_target": otp.delivery_target,
                        "delivery_method": otp.delivery_method.value,
                        "reason": "exception",
                        "error": str(e)
                    }
                )
                await self.log_repo.push(log)
            except Exception as log_error:
                logger.warning(f"Failed to log OTP send error: {log_error}")

    async def _syncToPostgres(
        self,
        otp: ManagementOtpDomain,
        operation: str,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> None:
        try:
            async with await self.uow_factory() as uow:
                if operation == "create":
                    await uow.otps.create(otp)
                elif operation == "update":
                    await uow.otps.update(otp)
                await uow.commit()
                logger.info(f"Successfully synced OTP {otp.sid} to PostgreSQL ({operation})")
        except Exception as e:
            logger.error(f"Failed to sync OTP {otp.sid} to PostgreSQL ({operation}): {e}")
            if retry_count < max_retries:
                logger.info(f"Retrying sync for OTP {otp.sid} (attempt {retry_count + 1}/{max_retries})")
                await self._syncToPostgres(otp, operation, retry_count + 1, max_retries)
            else:
                logger.error(f"Max retries exceeded for OTP {otp.sid} sync to PostgreSQL")
