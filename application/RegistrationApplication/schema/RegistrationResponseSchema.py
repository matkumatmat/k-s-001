from __future__ import annotations
from pydantic import BaseModel, Field
from uuid import UUID


class RegistrationOtpInfo(BaseModel):
    otpCode: str = Field(..., alias="otp_code")
    otpUrl: str = Field(..., alias="otp_url")
    expiresAt: str = Field(..., alias="expires_at")

    class Config:
        populate_by_name = True


class RegisterResponse(BaseModel):
    success: bool
    message: str
    userId: UUID | None = Field(None, alias="user_id")
    deliveryTarget: str = Field(..., alias="delivery_target")
    otpInfo: RegistrationOtpInfo = Field(..., alias="otp_info")

    class Config:
        populate_by_name = True


class VerifyRegistrationResponse(BaseModel):
    success: bool
    message: str
    userId: UUID | None = Field(None, alias="user_id")
    activeToken: str | None = Field(None, alias="active_token")
    refreshToken: str | None = Field(None, alias="refresh_token")
    deviceFingerprint: str | None = Field(None, alias="device_fingerprint")
    expiresAt: str | None = Field(None, alias="expires_at")

    class Config:
        populate_by_name = True
