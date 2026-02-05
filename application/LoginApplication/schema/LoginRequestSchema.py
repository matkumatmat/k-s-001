from __future__ import annotations
from pydantic import BaseModel, Field

class MetadataRequest(BaseModel):
    userAgent: str = Field(..., alias="user_agent", min_length=1)
    devicesWidth: int = Field(..., alias="devices_width", ge=1)
    devicesLength: int = Field(..., alias="devices_length", ge=1)
    ipAddress: str = Field(..., alias="ip_address", min_length=1)
    region: str = Field(..., min_length=1, max_length=10)
    lang: str = Field(..., min_length=2, max_length=10)

    class Config:
        populate_by_name = True

class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=3, description="Username or Email")
    password: str = Field(..., min_length=1)
    metadata: MetadataRequest

    class Config:
        populate_by_name = True

class TokenLoginRequest(BaseModel):
    accessToken: str = Field(..., alias="access_token", min_length=1)
    deviceFingerprint: str = Field(..., alias="device_fingerprint", min_length=1)
    metadata: MetadataRequest

    class Config:
        populate_by_name = True
