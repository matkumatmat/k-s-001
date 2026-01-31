from __future__ import annotations
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class MetadataRequest(BaseModel):
    userAgent: str = Field(..., alias="user_agent", min_length=1)
    devicesWidth: int = Field(..., alias="devices_width", ge=1)
    devicesLength: int = Field(..., alias="devices_length", ge=1)
    ipAddress: str = Field(..., alias="ip_address", min_length=1)
    region: str = Field(..., min_length=1, max_length=10)
    lang: str = Field(..., min_length=2, max_length=10)

    class Config:
        populate_by_name = True


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=4)
    email: str | None = None
    phone: str | None = None
    password: str = Field(..., min_length=6)
    firstName: str | None = Field(None, alias="first_name")
    lastName: str | None = Field(None, alias="last_name")
    deliveryMethod: str = Field(..., alias="delivery_method")
    merchantId: UUID = Field(..., alias="merchant_id")
    metadata: MetadataRequest

    class Config:
        populate_by_name = True


class VerifyRegistrationRequest(BaseModel):
    otpCode: str = Field(..., alias="otp_code", min_length=4)
    deliveryTarget: str = Field(..., alias="delivery_target")
    metadata: MetadataRequest

    class Config:
        populate_by_name = True
