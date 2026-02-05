from __future__ import annotations
from fastapi import Depends
from infrastructure.persistence.postgresql.connection import DatabaseConnection
from infrastructure.persistence.uow.PostgresUnitOfWork import PostgresUnitOfWork
from infrastructure.services.AuthenticationService import AuthenticationService
from application.OtpApplication.Dependencies import getOtpService
from application.SessionApplication.Dependencies import getSessionStorageService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import HTTPException, status
from domain.client.UserMetadataDomain import UserMetadataDomain
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.UserSessionDomain import UserSessionDomain
    from starlette.requests import Request
    from infrastructure.services.SessionStorageService import SessionStorageService
    from infrastructure.services.OtpService import OtpService

security = HTTPBearer()

async def getAuthenticationService(
    otpService: OtpService = Depends(getOtpService),
    sessionService: SessionStorageService = Depends(getSessionStorageService)
) -> AuthenticationService:

    async def uow_factory():
        db_session = DatabaseConnection.get_session_factory()()
        return PostgresUnitOfWork(db_session)

    return AuthenticationService(
        uow_factory=uow_factory,
        otp_service=otpService,
        session_service=sessionService
    )

async def get_current_session(
    request: Request,
    token: HTTPAuthorizationCredentials = Depends(security),
    service: SessionStorageService = Depends(getSessionStorageService)
) -> UserSessionDomain:
    # Extract metadata from headers to reconstruct fingerprint
    user_agent = request.headers.get("User-Agent", "unknown")
    ip_address = request.client.host if request.client else "unknown"

    # Custom headers for device info - client must send these for strict fingerprinting
    devices_width = int(request.headers.get("X-Devices-Width", 0))
    devices_length = int(request.headers.get("X-Devices-Length", 0))
    region = request.headers.get("X-Region", "unknown")
    lang = request.headers.get("Accept-Language", "en-US").split(',')[0]

    metadata = UserMetadataDomain(
        user_agent=user_agent,
        devices_width=devices_width,
        devices_length=devices_length,
        ip_address=ip_address,
        region=region,
        lang=lang
    )

    session = await service.validate_session(token.credentials, metadata)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token/session"
        )

    return session
