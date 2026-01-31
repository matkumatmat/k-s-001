from __future__ import annotations
from pydantic import BaseModel, Field
from uuid import UUID

class LoginResponse(BaseModel):
    success: bool
    message: str
    userId: UUID = Field(..., alias="user_id")
    activeToken: str = Field(..., alias="active_token")
    refreshToken: str = Field(..., alias="refresh_token")
    deviceFingerprint: str = Field(..., alias="device_fingerprint")
    expiresAt: str = Field(..., alias="expires_at")

    class Config:
        populate_by_name = True
