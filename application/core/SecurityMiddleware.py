from __future__ import annotations
from secure import (
    Secure,
    StrictTransportSecurity,
    XFrameOptions,
    XContentTypeOptions,
    ReferrerPolicy,
    ContentSecurityPolicy,
    CacheControl,
)
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

# Configure Secure Headers
# tailored for an API service
secure_headers = Secure(
    hsts=StrictTransportSecurity().include_subdomains().preload().max_age(31536000),
    xfo=XFrameOptions().deny(),
    xcto=XContentTypeOptions().nosniff(),
    referrer=ReferrerPolicy().strict_origin_when_cross_origin(),
    csp=ContentSecurityPolicy().default_src("'self'").frame_ancestors("'none'"),
    cache=CacheControl().no_store(), # Sensitive data should not be cached
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        secure_headers.set_headers(response)
        return response
