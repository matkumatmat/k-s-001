from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from application.SessionApplication.schema.SessionResponseSchema import (
    SessionResponse,
    SessionTokenResponse,
    SessionValidationResponse,
    SessionRevokeResponse,
    SessionRevokeAllResponse,
    MetadataResponse
)
from application.SessionApplication.Dependencies import getSessionStorageService
from domain.client.UserMetadataDomain import UserMetadataDomain
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.UserSessionDomain import UserSessionDomain
    from infrastructure.services.SessionStorageService import SessionStorageService
    from application.SessionApplication.schema.SessionRequestSchema import (
        CreateSessionRequest,
        ValidateSessionRequest,
        RefreshSessionRequest
    )
    from uuid import UUID

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _mapMetadataResponse(metadata: UserMetadataDomain) -> MetadataResponse:
    return MetadataResponse(
        user_agent=metadata.user_agent,
        devices_width=metadata.devices_width,
        devices_length=metadata.devices_length,
        ip_address=metadata.ip_address,
        region=metadata.region,
        lang=metadata.lang,
        device_type=metadata.device_type
    )


def _mapSessionResponse(session: UserSessionDomain) -> SessionResponse:
    return SessionResponse(
        sid=session.sid,
        user_id=session.user_id,
        active_token=session.active_token,
        refresh_token=session.refresh_token,
        device_fingerprint=session.device_fingerprint.encoded,
        expires_at=session.expiry.isoformat(),
        metadata=_mapMetadataResponse(session.metadata)
    )


def _mapTokenResponse(session: UserSessionDomain) -> SessionTokenResponse:
    return SessionTokenResponse(
        active_token=session.active_token,
        refresh_token=session.refresh_token,
        device_fingerprint=session.device_fingerprint.encoded,
        expires_at=session.expiry.isoformat()
    )


@router.post("/", response_model=SessionTokenResponse, status_code=status.HTTP_201_CREATED)
async def createSession(
    request: CreateSessionRequest,
    backgroundTasks: BackgroundTasks,
    service: SessionStorageService = Depends(getSessionStorageService)
):
    metadata = UserMetadataDomain(
        user_agent=request.metadata.userAgent,
        devices_width=request.metadata.devicesWidth,
        devices_length=request.metadata.devicesLength,
        ip_address=request.metadata.ipAddress,
        region=request.metadata.region,
        lang=request.metadata.lang
    )

    session = await service.create_session(
        user_id=request.userId,
        metadata=metadata,
        background_tasks=backgroundTasks,
        session_duration_days=request.sessionDurationDays
    )

    return _mapTokenResponse(session)


@router.post("/validate", response_model=SessionValidationResponse)
async def validateSession(
    request: ValidateSessionRequest,
    service: SessionStorageService = Depends(getSessionStorageService)
):
    metadata = UserMetadataDomain(
        user_agent=request.metadata.userAgent,
        devices_width=request.metadata.devicesWidth,
        devices_length=request.metadata.devicesLength,
        ip_address=request.metadata.ipAddress,
        region=request.metadata.region,
        lang=request.metadata.lang
    )

    session = await service.validate_session(
        active_token=request.activeToken,
        incoming_metadata=metadata
    )

    if session is None:
        return SessionValidationResponse(valid=False, session=None)

    return SessionValidationResponse(
        valid=True,
        session=_mapSessionResponse(session)
    )


@router.post("/refresh", response_model=SessionTokenResponse)
async def refreshSession(
    request: RefreshSessionRequest,
    backgroundTasks: BackgroundTasks,
    service: SessionStorageService = Depends(getSessionStorageService)
):
    session = await service.refresh_session(
        refresh_token=request.refreshToken,
        background_tasks=backgroundTasks
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return _mapTokenResponse(session)


@router.delete("/{sid}", response_model=SessionRevokeResponse)
async def revokeSession(
    sid: UUID,
    backgroundTasks: BackgroundTasks,
    service: SessionStorageService = Depends(getSessionStorageService)
):
    success = await service.revoke_session(
        sid=sid,
        background_tasks=backgroundTasks
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {sid} not found"
        )

    return SessionRevokeResponse(
        success=True,
        message=f"Session {sid} revoked successfully"
    )


@router.delete("/user/{userId}", response_model=SessionRevokeAllResponse)
async def revokeAllUserSessions(
    userId: UUID,
    backgroundTasks: BackgroundTasks,
    service: SessionStorageService = Depends(getSessionStorageService)
):
    count = await service.revoke_all_user_sessions(
        user_id=userId,
        background_tasks=backgroundTasks
    )

    return SessionRevokeAllResponse(
        success=True,
        revoked_count=count,
        message=f"Revoked {count} session(s) for user {userId}"
    )


@router.get("/{sid}", response_model=SessionResponse)
async def getSessionById(
    sid: UUID,
    service: SessionStorageService = Depends(getSessionStorageService)
):
    session = await service.get_session_by_id(sid)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {sid} not found"
        )

    return _mapSessionResponse(session)
