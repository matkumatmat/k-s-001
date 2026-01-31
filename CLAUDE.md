# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a **microservice for authentication and session management** built with strict **Clean Architecture** principles. The codebase enforces Pure OOP with no loose scripts or functional code.

### Layer Hierarchy (Strict Separation)

```
domain/           → Pure business logic (POPO - Plain Old Python Objects)
  ├── client/     → User-facing domain entities (sessions, metadata, fingerprints)
  └── management/ → System domain entities (OTP, value objects)

infrastructure/   → External integrations (never imported by domain)
  ├── persistence/
  │   ├── redis/       → Hot storage (sessions, OTP with TTL)
  │   ├── postgresql/  → Cold storage (audit, historical data)
  │   └── uow/         → Unit of Work pattern for transactions
  ├── messaging/       → Message providers (OTP delivery)
  └── services/        → Orchestration services (coordinate repositories + messaging)

application/      → API layer (FastAPI routers, schemas, DI)
  ├── SessionApplication/
  ├── OtpApplication/
  └── RegistrationApplication/
```

### Critical Architectural Rules

**Domain Layer (POPO Compliance):**
- NO external library dependencies beyond Python stdlib
- NO framework coupling (no FastAPI, SQLAlchemy, Redis in domain)
- Domain entities are pure dataclasses with business logic methods
- Factories handle complex object creation
- Repository interfaces (ABC) define contracts, never implementations

**Infrastructure Layer:**
- Implements domain repository interfaces
- Dual storage strategy: Redis (primary, TTL-based) + PostgreSQL (audit trail)
- Background tasks sync Redis → PostgreSQL with retry logic (3 attempts, exponential backoff)
- `UnitOfWork` manages PostgreSQL transactions only (Redis is atomic per-operation)

**Dependency Flow (Enforced):**
```
Application → Infrastructure → Domain
         ↓                    ↑
    (uses)              (implements)
```

Domain NEVER imports from infrastructure or application.

## Dual Storage Architecture

**Session Storage:**
- **Redis**: Source of truth for active sessions, auto-expire via TTL
- **PostgreSQL**: Audit log, eventual consistency acceptable
- Write flow: Redis immediate → Background task PostgreSQL sync

**OTP Storage:**
- **Redis**: Active OTPs with TTL = expiry_seconds
- **PostgreSQL**: Historical OTP attempts (fraud detection, analytics)
- Verification checks Redis first, fallback to PostgreSQL

**UoW Factory Pattern:**
```python
async def uow_factory():
    db_session = DatabaseConnection.get_session_factory()()
    return PostgresUnitOfWork(db_session)

# Usage in services:
async with await self.uow_factory() as uow:
    await uow.sessions.create(session)
    await uow.commit()
```

**Critical**: Always `await self.uow_factory()` - the factory itself is async.

## Device Fingerprinting

**Value Object Pattern:**
- `DeviceFingerprintVO` (immutable, frozen dataclass)
- Generates deterministic fingerprint from metadata
- Properties: `.raw` (string), `.encoded` (base64), `.matches(other)`
- Used for session binding (not sole auth factor - easily spoofed)

**Auto Device Detection:**
```python
# UserMetadataDomain.device_type property
< 768px          → ManagementDevices.MOBILE
768px - 1023px   → ManagementDevices.TABLET
≥ 1024px         → ManagementDevices.DESKTOP
```

## OTP System

**Two-Output Design:**
1. `otp_code` - Numeric code for manual entry
2. `otp_url` - Pre-filled verification link

**Message Provider Interface:**
- `ConsoleMessageProvider` - Dev mode (prints to console/logs)
- Extensible: Create providers for Twilio, SendGrid, WhatsApp
- All providers implement `IMessageProvider.sendOtp()` and `supportsMethod()`

**OTP Flow:**
```
1. OtpService.createOtp() → Generate code + URL
2. Store in Redis with TTL
3. Background task: Sync to PostgreSQL
4. Background task: Send via MessageProvider
5. OtpService.verifyOtp() → Check code + target + expiry + !used
6. Mark as used, update both storages
```

## Development Commands

**Start Services:**
```bash
docker-compose up -d           # Start Redis + PostgreSQL
docker-compose down            # Stop services
docker-compose down -v         # Stop + remove volumes
```

**Run Application:**
```bash
poetry install --no-root       # Install dependencies
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Linting:**
```bash
poetry run ruff check .        # Lint all files
poetry run ruff format .       # Format code
poetry run mypy .              # Type checking
```

**Environment Setup:**
- Copy `.env` and configure:
  - `DATABASE_URL` - PostgreSQL connection string
  - `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
  - `OTP_URL_PREFIX`, `OTP_CODE_LEN`, `OTP_EXPIRES_SECONDS`

## Naming Conventions

**Files:** PascalCase (e.g., `SessionRouter.py`, `UserSessionDomain.py`)
**Functions/Methods:** camelCase (e.g., `createSession()`, `verifyOtp()`)
**Classes:** PascalCase
**Private methods:** Prefix with `_` (e.g., `_syncToPostgres()`)

**API Field Naming:**
- Request/Response schemas use `camelCase` with `alias` for snake_case API
- Example: `userId: UUID = Field(..., alias="user_id")`
- Internal domain uses snake_case

## Testing Domain Logic

Domain files include `__main__` test blocks (commented out). To run:

```python
# Uncomment test block at end of file, then:
python -m domain.client.UserSessionDomain
python -m domain.client.DeviceFingerprintVO
python -m domain.management.OtpAuthenticationDomain
```

Tests cover happy paths, edge cases, validation errors, and business logic.

## Critical Patterns

**Factory Pattern:**
- `UserSessionFactory.create_new_session()` - New sessions with auto-generated tokens
- `UserSessionFactory.create_from_persistence()` - Reconstruct from database
- `OtpAuthenticationFactory.createOtp()` - Generate OTP with code + URL

**Repository Pattern:**
- All repositories implement async interface (ABC)
- Methods: `create()`, `getById()`, `update()`, `delete()`, `exists()`
- Redis repos use pipeline for atomic multi-key operations

**Service Pattern:**
- Orchestrate multiple repositories + external services
- Accept `BackgroundTasks` for async PostgreSQL sync
- Handle retries with exponential backoff
- Never throw exceptions for expected failures (return `None` or `False`)

## PostgreSQL Tables (Migration Needed)

Tables not yet created (background sync will fail until created):

```sql
CREATE TABLE user_sessions (
    sid UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    active TIMESTAMP WITH TIME ZONE NOT NULL,
    expiry TIMESTAMP WITH TIME ZONE NOT NULL,
    active_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    device_fingerprint VARCHAR(255) NOT NULL,
    metadata_* ...  -- Individual metadata fields
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE otp_authentications (
    sid UUID PRIMARY KEY,
    otp_code VARCHAR(10) NOT NULL,
    otp_url TEXT NOT NULL,
    delivery_target VARCHAR(255) NOT NULL,
    delivery_method VARCHAR(50) NOT NULL,
    purpose VARCHAR(50) NOT NULL,
    expired_at TIMESTAMP WITH TIME ZONE NOT NULL,
    merchant_id UUID NOT NULL,
    used BOOLEAN,
    used_at TIMESTAMP WITH TIME ZONE,
    user_id UUID,
    identifier VARCHAR(255),
    -- Add indexes on: delivery_target, purpose, expired_at, user_id
);
```

Use Alembic for migrations (already configured in dependencies).

## API Documentation

Live docs: http://localhost:8000/docs

**Session Endpoints:**
- `POST /sessions` - Create session (login)
- `POST /sessions/validate` - Validate token + fingerprint
- `POST /sessions/refresh` - Refresh tokens
- `DELETE /sessions/{sid}` - Revoke session
- `GET /sessions/{sid}` - Get session details

**OTP Endpoints:**
- `POST /otp/send` - Send OTP to target
- `POST /otp/verify` - Verify OTP code
- `GET /otp/{sid}` - Get OTP details

**Registration Endpoints:**
- `POST /registration/register` - Register user + send OTP
- `POST /registration/verify` - Verify OTP + create session

## Important Constraints

**Domain Purity:**
- No `import fastapi`, `import sqlalchemy`, `import redis` in `domain/`
- Use `if TYPE_CHECKING:` for type hints that would violate purity
- Value Objects must be `frozen=True` (immutable)

**Async Everywhere:**
- All repository methods are `async`
- All service methods are `async`
- Use `await` for I/O operations
- Background tasks run fire-and-forget (log errors, don't throw)

**Security:**
- Device fingerprints are for session binding, NOT authentication
- Base64 encoding is NOT encryption (consider HMAC for tamper-proof tokens)
- OTP TTL enforced in Redis (expires automatically)
- Session tokens use `secrets.token_urlsafe(32)` (256-bit entropy)

**Error Handling in Services:**
- Return `None` for "not found" scenarios
- Return `False` for "operation failed" scenarios
- Only raise exceptions for unexpected errors (connection failures, programming errors)
- Let routers convert `None`/`False` to appropriate HTTP responses
