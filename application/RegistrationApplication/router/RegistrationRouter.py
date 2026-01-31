from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from application.RegistrationApplication.schema.RegistrationResponseSchema import (
    RegisterResponse,
    VerifyRegistrationResponse,
    RegistrationOtpInfo
)
from application.Dependencies import getAuthenticationService
from domain.management.ValueObject import AuthenticationProvider
from domain.client.UserMetadataDomain import UserMetadataDomain
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.services.AuthenticationService import AuthenticationService
    from application.RegistrationApplication.schema.RegistrationRequestSchema import (
        RegisterRequest,
        VerifyRegistrationRequest
    )

router = APIRouter(prefix="/registration", tags=["Registration"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def registerUser(
    request: RegisterRequest,
    backgroundTasks: BackgroundTasks,
    authService: AuthenticationService = Depends(getAuthenticationService)
):
    if not request.email and not request.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone must be provided"
        )

    try:
        delivery_method = AuthenticationProvider(request.deliveryMethod)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid delivery method: {request.deliveryMethod}"
        )

    delivery_target = request.email if delivery_method == AuthenticationProvider.EMAIL else request.phone

    if not delivery_target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delivery target not provided for method {delivery_method.value}"
        )

    try:
        otp = await authService.register_user(
            username=request.username,
            password=request.password,
            email=request.email,
            phone=request.phone,
            first_name=request.firstName,
            last_name=request.lastName,
            delivery_method=delivery_method,
            delivery_target=delivery_target,
            merchant_id=request.merchantId,
            metadata_info=request.metadata.model_dump(by_alias=True),
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
async def verifyRegistration(
    request: VerifyRegistrationRequest,
    backgroundTasks: BackgroundTasks,
    authService: AuthenticationService = Depends(getAuthenticationService)
):
    metadata = UserMetadataDomain(
        user_agent=request.metadata.userAgent,
        devices_width=request.metadata.devicesWidth,
        devices_length=request.metadata.devicesLength,
        ip_address=request.metadata.ipAddress,
        region=request.metadata.region,
        lang=request.metadata.lang
    )

    session = await authService.verify_registration(
        otp_code=request.otpCode,
        delivery_target=request.deliveryTarget,
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
