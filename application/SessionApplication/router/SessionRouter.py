from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from application.SessionApplication.schema.SessionResponseSchema import (
    SessionResponse,
    SessionTokenResponse,
    SessionValidationResponse,
    SessionRevokeResponse,
    SessionRevokeAllResponse,
    MetadataResponse
)
from application.SessionApplication.schema.SessionRequestSchema import (
    CreateSessionRequest,
    ValidateSessionRequest,
    RefreshSessionRequest
)
from application.SessionApplication.Dependencies import getSessionStorageService
from application.core.RateLimiter import limiter
from application.core.SecurityConfig import security_config
from domain.client.UserMetadataDomain import UserMetadataDomain
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.UserSessionDomain import UserSessionDomain
    from infrastructure.services.SessionStorageService import SessionStorageService

security = HTTPBearer()

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
@limiter.limit(security_config.RATE_LIMIT_DEFAULT)
async def createSession(
    request: Request,
    createRequest: CreateSessionRequest,
    backgroundTasks: BackgroundTasks,
    service: SessionStorageService = Depends(getSessionStorageService)
):
    metadata = UserMetadataDomain(
        user_agent=createRequest.metadata.userAgent,
        devices_width=createRequest.metadata.devicesWidth,
        devices_length=createRequest.metadata.devicesLength,
        ip_address=createRequest.metadata.ipAddress,
        region=createRequest.metadata.region,
        lang=createRequest.metadata.lang
    )

    session = await service.create_session(
        user_id=createRequest.userId,
        metadata=metadata,
        background_tasks=backgroundTasks,
        session_duration_days=createRequest.sessionDurationDays
    )

    return _mapTokenResponse(session)


@router.post("/validate", response_model=SessionValidationResponse)
@limiter.limit(security_config.RATE_LIMIT_DEFAULT)
async def validateSession(
    request: Request,
    validateRequest: ValidateSessionRequest,
    service: SessionStorageService = Depends(getSessionStorageService)
):
    metadata = UserMetadataDomain(
        user_agent=validateRequest.metadata.userAgent,
        devices_width=validateRequest.metadata.devicesWidth,
        devices_length=validateRequest.metadata.devicesLength,
        ip_address=validateRequest.metadata.ipAddress,
        region=validateRequest.metadata.region,
        lang=validateRequest.metadata.lang
    )

    session = await service.validate_session(
        active_token=validateRequest.activeToken,
        incoming_metadata=metadata
    )

    if session is None:
        return SessionValidationResponse(valid=False, session=None)

    return SessionValidationResponse(
        valid=True,
        session=_mapSessionResponse(session)
    )


@router.post("/refresh", response_model=SessionTokenResponse)
@limiter.limit(security_config.RATE_LIMIT_DEFAULT)
async def refreshSession(
    request: Request,
    refreshRequest: RefreshSessionRequest,
    backgroundTasks: BackgroundTasks,
    service: SessionStorageService = Depends(getSessionStorageService)
):
    session = await service.refresh_session(
        refresh_token=refreshRequest.refreshToken,
        background_tasks=backgroundTasks
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return _mapTokenResponse(session)


@router.delete("/{sid}", response_model=SessionRevokeResponse)
@limiter.limit(security_config.RATE_LIMIT_DEFAULT)
async def revokeSession(
    request: Request,
    sid: UUID,
    backgroundTasks: BackgroundTasks,
    service: SessionStorageService = Depends(getSessionStorageService),
    credentials: HTTPAuthorizationCredentials = Security(security)
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
@limiter.limit(security_config.RATE_LIMIT_DEFAULT)
async def revokeAllUserSessions(
    request: Request,
    userId: UUID,
    backgroundTasks: BackgroundTasks,
    service: SessionStorageService = Depends(getSessionStorageService),
    credentials: HTTPAuthorizationCredentials = Security(security)
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
@limiter.limit(security_config.RATE_LIMIT_DEFAULT)
async def getSessionById(
    request: Request,
    sid: UUID,
    service: SessionStorageService = Depends(getSessionStorageService),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    session = await service.get_session_by_id(sid)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {sid} not found"
        )

    return _mapSessionResponse(session)
