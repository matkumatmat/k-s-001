from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from application.RegistrationApplication.schema.RegistrationResponseSchema import (
    RegisterResponse,
    VerifyRegistrationResponse,
    RegistrationOtpInfo
)
from application.RegistrationApplication.schema.RegistrationRequestSchema import (
    RegisterRequest,
    VerifyRegistrationRequest
)
from application.Dependencies import getAuthenticationService
from application.core.RateLimiter import limiter
from application.core.SecurityConfig import security_config
from domain.management.ValueObject import AuthenticationProvider
from domain.client.UserMetadataDomain import UserMetadataDomain
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.services.AuthenticationService import AuthenticationService

router = APIRouter(prefix="/registration", tags=["Registration"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(security_config.RATE_LIMIT_OTP)
async def registerUser(
    request: Request,
    regRequest: RegisterRequest,
    backgroundTasks: BackgroundTasks,
    authService: AuthenticationService = Depends(getAuthenticationService)
):
    if not regRequest.email and not regRequest.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone must be provided"
        )

    try:
        delivery_method = AuthenticationProvider(regRequest.deliveryMethod)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid delivery method: {regRequest.deliveryMethod}"
        )

    delivery_target = regRequest.email if delivery_method == AuthenticationProvider.EMAIL else regRequest.phone

    if not delivery_target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery target not provided for method {delivery_method.value}"
        )

    try:
        otp = await authService.register_user(
            username=regRequest.username,
            password=regRequest.password,
            email=regRequest.email,
            phone=regRequest.phone,
            first_name=regRequest.firstName,
            last_name=regRequest.lastName,
            delivery_method=delivery_method,
            delivery_target=delivery_target,
            merchant_id=regRequest.merchantId,
            metadata_info=regRequest.metadata.model_dump(by_alias=True),
            background_tasks=backgroundTasks
        )
    except ValueError as e:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return RegisterResponse(
        success=True,
        message=f"OTP sent to {delivery_target}",
        user_id=otp.user_id,
        delivery_target=delivery_target,
        otp_info=RegistrationOtpInfo(
            otp_code=otp.otp_code,
            otp_url=otp.otp_url,
            expires_at=otp.expired_at.isoformat()
        )
    )


@router.post("/verify", response_model=VerifyRegistrationResponse)
@limiter.limit(security_config.RATE_LIMIT_DEFAULT)
async def verifyRegistration(
    request: Request,
    verifyRequest: VerifyRegistrationRequest,
    backgroundTasks: BackgroundTasks,
    authService: AuthenticationService = Depends(getAuthenticationService)
):
    metadata = UserMetadataDomain(
        user_agent=verifyRequest.metadata.userAgent,
        devices_width=verifyRequest.metadata.devicesWidth,
        devices_length=verifyRequest.metadata.devicesLength,
        ip_address=verifyRequest.metadata.ipAddress,
        region=verifyRequest.metadata.region,
        lang=verifyRequest.metadata.lang
    )

    session = await authService.verify_registration(
        otp_code=verifyRequest.otpCode,
        delivery_target=verifyRequest.deliveryTarget,
        metadata=metadata,
        background_tasks=backgroundTasks
    )

    if session is None:
        return VerifyRegistrationResponse(
            success=False,
            message="Invalid or expired OTP, or verification failed",
            user_id=None,
            active_token=None,
            refresh_token=None,
            device_fingerprint=None,
            expires_at=None
        )

    return VerifyRegistrationResponse(
        success=True,
        message="Registration verified successfully",
        user_id=session.user_id,
        active_token=session.active_token,
        refresh_token=session.refresh_token,
        device_fingerprint=session.device_fingerprint.encoded,
        expires_at=session.expiry.isoformat()
    )
