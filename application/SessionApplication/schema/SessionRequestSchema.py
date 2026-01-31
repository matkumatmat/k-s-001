from __future__ import annotations
from pydantic import BaseModel, Field
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


class CreateSessionRequest(BaseModel):
    userId: UUID = Field(..., alias="user_id")
    metadata: MetadataRequest
    sessionDurationDays: int = Field(default=30, alias="session_duration_days", ge=1, le=365)

    class Config:
        populate_by_name = True


class ValidateSessionRequest(BaseModel):
    activeToken: str = Field(..., alias="active_token", min_length=1)
    metadata: MetadataRequest

    class Config:
        populate_by_name = True


class RefreshSessionRequest(BaseModel):
    refreshToken: str = Field(..., alias="refresh_token", min_length=1)

    class Config:
        populate_by_name = True
