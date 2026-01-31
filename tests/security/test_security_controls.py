import os
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

# Import app
from main import app
from application.core.RateLimiter import get_key_ip_fingerprint

client = TestClient(app)

def test_security_headers_root():
    """Verify security headers are present on root endpoint."""
    response = client.get("/")
    assert response.status_code == 200

    headers = response.headers
    # Check for HSTS
    assert "strict-transport-security" in headers
    assert "max-age=31536000" in headers["strict-transport-security"]

    # Check X-Frame-Options
    assert "x-frame-options" in headers
    assert headers["x-frame-options"] == "DENY"

    # Check CSP
    assert "content-security-policy" in headers
    assert "default-src 'self'" in headers["content-security-policy"]

def test_rate_limit_key_logic():
    """Verify the Rate Limiter key generation logic (IP x Fingerprint)."""
    # Case 1: Fallback to constructed fingerprint
    scope = {
        "type": "http",
        "client": ("1.2.3.4", 1234),
        "headers": [
            (b"user-agent", b"test-agent"),
            (b"x-devices-width", b"100"),
            (b"x-devices-length", b"200"),
            (b"accept-language", b"en"),
        ]
    }
    req = Request(scope)
    key = get_key_ip_fingerprint(req)
    # Expected: IP + Constructed Fingerprint
    assert key == "1.2.3.4:test-agent|100x200|en"

    # Case 2: Explicit Fingerprint Header
    scope2 = {
        "type": "http",
        "client": ("5.6.7.8", 1234),
        "headers": [
            (b"x-device-fingerprint", b"explicit-fp"),
            (b"user-agent", b"ignore-me"),
        ]
    }
    req2 = Request(scope2)
    key2 = get_key_ip_fingerprint(req2)
    # Expected: IP + Explicit Fingerprint
    assert key2 == "5.6.7.8:explicit-fp"

# Integration tests for rate limiting are skipped because Redis is not available in this environment.
# The ConnectionError observed during development confirms that the Limiter is active and attempting to connect.
