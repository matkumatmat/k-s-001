from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response, Request
from application.LoginApplication.schema.LoginResponseSchema import LoginResponse
from application.LoginApplication.schema.LoginRequestSchema import LoginRequest, TokenLoginRequest
from application.Dependencies import getAuthenticationService
from application.core.RateLimiter import limiter
from application.core.SecurityConfig import security_config
from domain.client.UserMetadataDomain import UserMetadataDomain
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.services.AuthenticationService import AuthenticationService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
@limiter.limit(security_config.RATE_LIMIT_DEFAULT)
async def login(
    request: Request,
    loginRequest: LoginRequest,
    response: Response,
    backgroundTasks: BackgroundTasks,
    authService: AuthenticationService = Depends(getAuthenticationService)
):
    metadata = UserMetadataDomain(
        user_agent=loginRequest.metadata.userAgent,
        devices_width=loginRequest.metadata.devicesWidth,
        devices_length=loginRequest.metadata.devicesLength,
        ip_address=loginRequest.metadata.ipAddress,
        region=loginRequest.metadata.region,
        lang=loginRequest.metadata.lang
    )

    session = await authService.login(
        identifier=loginRequest.identifier,
        password=loginRequest.password,
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
@limiter.limit(security_config.RATE_LIMIT_DEFAULT)
async def loginByToken(
    request: Request,
    tokenRequest: TokenLoginRequest,
    response: Response,
    authService: AuthenticationService = Depends(getAuthenticationService)
):
    metadata = UserMetadataDomain(
        user_agent=tokenRequest.metadata.userAgent,
        devices_width=tokenRequest.metadata.devicesWidth,
        devices_length=tokenRequest.metadata.devicesLength,
        ip_address=tokenRequest.metadata.ipAddress,
        region=tokenRequest.metadata.region,
        lang=tokenRequest.metadata.lang
    )

    session = await authService.login_by_token(
        access_token=tokenRequest.accessToken,
        metadata=metadata
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Verify fingerprint matches what client claims
    if tokenRequest.deviceFingerprint != session.device_fingerprint.encoded:
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
