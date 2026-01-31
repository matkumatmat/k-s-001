from __future__ import annotations
from pydantic import BaseModel, Field
from uuid import UUID


class OtpResponse(BaseModel):
    sid: UUID
    otpCode: str = Field(..., alias="otp_code")
    otpUrl: str = Field(..., alias="otp_url")
    deliveryTarget: str = Field(..., alias="delivery_target")
    deliveryMethod: str = Field(..., alias="delivery_method")
    purpose: str
    expiresAt: str = Field(..., alias="expires_at")

    class Config:
        populate_by_name = True


class VerifyOtpResponse(BaseModel):
    success: bool
    message: str
    otp: OtpResponse | None = None

    class Config:
        populate_by_name = True
