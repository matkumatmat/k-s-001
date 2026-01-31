from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from uuid import uuid4
from application.RegistrationApplication.schema.RegistrationRequestSchema import (
    RegisterRequest,
    VerifyRegistrationRequest
)
from application.RegistrationApplication.schema.RegistrationResponseSchema import (
    RegisterResponse,
    VerifyRegistrationResponse,
    RegistrationOtpInfo
)
from application.OtpApplication.Dependencies import getOtpService
from application.SessionApplication.Dependencies import getSessionStorageService
from infrastructure.services.OtpService import OtpService
from infrastructure.services.SessionStorageService import SessionStorageService
from domain.management.ValueObject import AuthenticationOtpPurpose, AuthenticationProvider
from domain.client.UserMetadataDomain import UserMetadataDomain

router = APIRouter(prefix="/registration", tags=["Registration"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def registerUser(
    request: RegisterRequest,
    backgroundTasks: BackgroundTasks,
    otpService: OtpService = Depends(getOtpService)
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

    temp_user_id = uuid4()

    otp = await otpService.createOtp(
        delivery_target=delivery_target,
        delivery_method=delivery_method,
        purpose=AuthenticationOtpPurpose.REGISTRATION,
        merchant_id=request.merchantId,
        background_tasks=backgroundTasks,
        user_id=temp_user_id,
        identifier=request.username
    )

    return RegisterResponse(
        success=True,
        message=f"OTP sent to {delivery_target}",
        user_id=temp_user_id,
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
    otpService: OtpService = Depends(getOtpService),
    sessionService: SessionStorageService = Depends(getSessionStorageService)
):
    otp = await otpService.verifyOtp(
        otp_code=request.otpCode,
        delivery_target=request.deliveryTarget,
        background_tasks=backgroundTasks
    )

    if otp is None:
        return VerifyRegistrationResponse(
            success=False,
            message="Invalid or expired OTP",
            user_id=None,
            active_token=None,
            refresh_token=None,
            device_fingerprint=None,
            expires_at=None
        )

    if otp.purpose != AuthenticationOtpPurpose.REGISTRATION:
        return VerifyRegistrationResponse(
            success=False,
            message="OTP not valid for registration",
            user_id=None,
            active_token=None,
            refresh_token=None,
            device_fingerprint=None,
            expires_at=None
        )

    if not otp.user_id:
        return VerifyRegistrationResponse(
            success=False,
            message="Invalid OTP data",
            user_id=None,
            active_token=None,
            refresh_token=None,
            device_fingerprint=None,
            expires_at=None
        )

    metadata = UserMetadataDomain(
        user_agent=request.metadata.userAgent,
        devices_width=request.metadata.devicesWidth,
        devices_length=request.metadata.devicesLength,
        ip_address=request.metadata.ipAddress,
        region=request.metadata.region,
        lang=request.metadata.lang
    )

    session = await sessionService.create_session(
        user_id=otp.user_id,
        metadata=metadata,
        background_tasks=backgroundTasks,
        session_duration_days=30
    )

    return VerifyRegistrationResponse(
        success=True,
        message="Registration verified successfully",
        user_id=otp.user_id,
        active_token=session.active_token,
        refresh_token=session.refresh_token,
        device_fingerprint=session.device_fingerprint.encoded,
        expires_at=session.expiry.isoformat()
    )
