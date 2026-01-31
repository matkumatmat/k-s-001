## 2026-02-01 - [Rate Limiting Strategy & Secure Headers]
**Vulnerability:** Lack of rate limiting on sensitive endpoints (OTP, Login) allowed for potential enumeration and DoS attacks.
**Learning:** `slowapi` requires the `Request` object to be explicitly injected into FastAPI path operations to function correctly. Additionally, `secure` library v1.x uses positional arguments for configuration, unlike previous versions which accepted keyword arguments or chained methods on the instance.
**Prevention:** Implemented a reusable `RateLimiter` module with a custom key function (`IP x Device Fingerprint`) that can be applied via decorators. Future endpoints should use this pattern: `@limiter.limit(security_config.RATE_LIMIT_DEFAULT)`.
