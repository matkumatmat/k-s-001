from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from application.OtpApplication.schema.OtpResponseSchema import OtpResponse, VerifyOtpResponse
from application.OtpApplication.Dependencies import getOtpService
from domain.management.ValueObject import AuthenticationOtpPurpose, AuthenticationProvider
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.management.OtpAuthenticationDomain import ManagementOtpDomain
    from infrastructure.services.OtpService import OtpService
    from application.OtpApplication.schema.OtpRequestSchema import SendOtpRequest, VerifyOtpRequest
    from uuid import UUID

router = APIRouter(prefix="/otp", tags=["OTP"])


def _mapOtpResponse(otp: ManagementOtpDomain) -> OtpResponse:
    return OtpResponse(
        sid=otp.sid,
        otp_code=otp.otp_code,
        otp_url=otp.otp_url,
        delivery_target=otp.delivery_target,
        delivery_method=otp.delivery_method.value,
        purpose=otp.purpose.value,
        expires_at=otp.expired_at.isoformat()
    )


@router.post("/send", response_model=OtpResponse, status_code=status.HTTP_201_CREATED)
async def sendOtp(
    request: SendOtpRequest,
    backgroundTasks: BackgroundTasks,
    service: OtpService = Depends(getOtpService)
):
    try:
        delivery_method = AuthenticationProvider(request.deliveryMethod)
        purpose = AuthenticationOtpPurpose(request.purpose)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid delivery method or purpose: {e!s}"
        )

    otp = await service.createOtp(
        delivery_target=request.deliveryTarget,
        delivery_method=delivery_method,
        purpose=purpose,
        merchant_id=request.merchantId,
        background_tasks=backgroundTasks,
        user_id=request.userId,
        identifier=request.identifier
    )

    return _mapOtpResponse(otp)


@router.post("/verify", response_model=VerifyOtpResponse)
async def verifyOtp(
    request: VerifyOtpRequest,
    backgroundTasks: BackgroundTasks,
    service: OtpService = Depends(getOtpService)
):
    otp = await service.verifyOtp(
        otp_code=request.otpCode,
        delivery_target=request.deliveryTarget,
        background_tasks=backgroundTasks
    )

    if otp is None:
        return VerifyOtpResponse(
            success=False,
            message="Invalid or expired OTP",
            otp=None
        )

    return VerifyOtpResponse(
        success=True,
        message="OTP verified successfully",
        otp=_mapOtpResponse(otp)
    )


@router.get("/{sid}", response_model=OtpResponse)
async def getOtpById(
    sid: UUID,
    service: OtpService = Depends(getOtpService)
):
    otp = await service.getOtpById(sid)

    if otp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OTP {sid} not found"
        )

    return _mapOtpResponse(otp)
