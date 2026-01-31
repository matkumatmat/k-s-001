from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from application.LoginApplication.schema.LoginResponseSchema import LoginResponse
from application.Dependencies import getAuthenticationService
from domain.client.UserMetadataDomain import UserMetadataDomain
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.services.AuthenticationService import AuthenticationService
    from application.LoginApplication.schema.LoginRequestSchema import LoginRequest, TokenLoginRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    response: Response,
    backgroundTasks: BackgroundTasks,
    authService: AuthenticationService = Depends(getAuthenticationService)
):
    metadata = UserMetadataDomain(
        user_agent=request.metadata.userAgent,
        devices_width=request.metadata.devicesWidth,
        devices_length=request.metadata.devicesLength,
        ip_address=request.metadata.ipAddress,
        region=request.metadata.region,
        lang=request.metadata.lang
    )

    session = await authService.login(
        identifier=request.identifier,
        password=request.password,
        metadata=metadata,
        background_tasks=backgroundTasks
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Set Cookie
    response.set_cookie(
        key="access_token",
        value=session.active_token,
        httponly=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60 # 30 days
    )

    return LoginResponse(
        success=True,
        message="Login successful",
        user_id=session.user_id,
        active_token=session.active_token,
        refresh_token=session.refresh_token,
        device_fingerprint=session.device_fingerprint.encoded,
        expires_at=session.expiry.isoformat()
    )


@router.post("/login/token", response_model=LoginResponse)
async def loginByToken(
    request: TokenLoginRequest,
    response: Response,
    authService: AuthenticationService = Depends(getAuthenticationService)
):
    metadata = UserMetadataDomain(
        user_agent=request.metadata.userAgent,
        devices_width=request.metadata.devicesWidth,
        devices_length=request.metadata.devicesLength,
        ip_address=request.metadata.ipAddress,
        region=request.metadata.region,
        lang=request.metadata.lang
    )

    session = await authService.login_by_token(
        access_token=request.accessToken,
        metadata=metadata
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Verify fingerprint matches what client claims
    if request.deviceFingerprint != session.device_fingerprint.encoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device fingerprint mismatch"
        )

    # Set Cookie (refresh it)
    response.set_cookie(
        key="access_token",
        value=session.active_token,
        httponly=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60
    )

    return LoginResponse(
        success=True,
        message="Token login successful",
        user_id=session.user_id,
        active_token=session.active_token,
        refresh_token=session.refresh_token,
        device_fingerprint=session.device_fingerprint.encoded,
        expires_at=session.expiry.isoformat()
    )
