from __future__ import annotations
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class MetadataResponse(BaseModel):
    userAgent: str = Field(..., alias="user_agent")
    devicesWidth: int = Field(..., alias="devices_width")
    devicesLength: int = Field(..., alias="devices_length")
    ipAddress: str = Field(..., alias="ip_address")
    region: str
    lang: str
    deviceType: str = Field(..., alias="device_type")

    class Config:
        populate_by_name = True


class SessionResponse(BaseModel):
    sid: UUID
    userId: UUID = Field(..., alias="user_id")
    activeToken: str = Field(..., alias="active_token")
    refreshToken: str = Field(..., alias="refresh_token")
    deviceFingerprint: str = Field(..., alias="device_fingerprint")
    expiresAt: str = Field(..., alias="expires_at")
    metadata: MetadataResponse

    class Config:
        populate_by_name = True


class SessionTokenResponse(BaseModel):
    activeToken: str = Field(..., alias="active_token")
    refreshToken: str = Field(..., alias="refresh_token")
    deviceFingerprint: str = Field(..., alias="device_fingerprint")
    expiresAt: str = Field(..., alias="expires_at")

    class Config:
        populate_by_name = True


class SessionValidationResponse(BaseModel):
    valid: bool
    session: SessionResponse | None = None

    class Config:
        populate_by_name = True


class SessionRevokeResponse(BaseModel):
    success: bool
    message: str


class SessionRevokeAllResponse(BaseModel):
    success: bool
    revokedCount: int = Field(..., alias="revoked_count")
    message: str

    class Config:
        populate_by_name = True
