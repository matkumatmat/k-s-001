from __future__ import annotations
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from infrastructure.persistence.redis.connection import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from application.core.SecurityConfig import security_config

def get_key_ip_fingerprint(request: Request) -> str:
    """
    Constructs a rate limit key based on IP and Device Fingerprint.
    """
    ip = get_remote_address(request)

    # Try to get explicit fingerprint from header (if client sends it)
    fingerprint = request.headers.get("X-Device-Fingerprint")

    if not fingerprint:
        # Fallback: Construct a pseudo-fingerprint from available device headers
        # These headers are used in Dependencies.py for UserMetadata
        user_agent = request.headers.get("User-Agent", "unknown")
        width = request.headers.get("X-Devices-Width", "0")
        length = request.headers.get("X-Devices-Length", "0")
        lang = request.headers.get("Accept-Language", "unknown")

        fingerprint = f"{user_agent}|{width}x{length}|{lang}"

    return f"{ip}:{fingerprint}"

# Construct Redis URL
if security_config.REDIS_URL:
    storage_url = security_config.REDIS_URL
else:
    auth_part = f":{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
    storage_url = f"redis://{auth_part}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

limiter = Limiter(
    key_func=get_key_ip_fingerprint,
    storage_uri=storage_url,
    headers_enabled=True # Return X-RateLimit headers
)
