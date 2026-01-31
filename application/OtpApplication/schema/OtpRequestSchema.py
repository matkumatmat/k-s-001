from __future__ import annotations
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class SendOtpRequest(BaseModel):
    deliveryTarget: str = Field(..., alias="delivery_target", min_length=1)
    deliveryMethod: str = Field(..., alias="delivery_method")
    purpose: str = Field(...)
    merchantId: UUID = Field(..., alias="merchant_id")
    userId: UUID | None = Field(None, alias="user_id")
    identifier: str | None = Field(None)

    class Config:
        populate_by_name = True


class VerifyOtpRequest(BaseModel):
    otpCode: str = Field(..., alias="otp_code", min_length=4, max_length=10)
    deliveryTarget: str = Field(..., alias="delivery_target", min_length=1)

    class Config:
        populate_by_name = True
