from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class SecurityConfig(BaseSettings):
    RATE_LIMIT_OTP: str = Field("3/hour", description="Rate limit for OTP endpoints")
    RATE_LIMIT_DEFAULT: str = Field("10/minute", description="Default rate limit for other endpoints")
    SECURE_HEADERS: bool = Field(True, description="Enable security headers")

    # Redis config for Rate Limiter (reuse existing env vars if possible or define new)
    # We will construct the REDIS_URL dynamically if not provided, or allow override
    REDIS_URL: str | None = Field(None, description="Redis URL for rate limiting storage")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

security_config = SecurityConfig()
