from __future__ import annotations
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text
from application.SessionApplication.router.SessionRouter import router as session_router
from application.OtpApplication.router.OtpRouter import router as otp_router
from application.RegistrationApplication.router.RegistrationRouter import router as registration_router
from application.LoginApplication.router.LoginRouter import router as login_router
from infrastructure.persistence.redis.connection import RedisConnection
from infrastructure.persistence.postgresql.connection import DatabaseConnection
from infrastructure.persistence.redis.RedisLogRepository import RedisLogRepository
from infrastructure.persistence.uow.PostgresUnitOfWork import PostgresUnitOfWork
from infrastructure.services.LogSyncService import LogSyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_background_log_sync():
    """Background task to sync logs from Redis to PostgreSQL every 30 minutes."""
    while True:
        try:
            # Wait for 30 minutes (1800 seconds)
            await asyncio.sleep(1800)

            logger.info("Starting scheduled log sync...")

            # Initialize dependencies
            redis_client = await RedisConnection.get_client()
            redis_repo = RedisLogRepository(redis_client)

            async def uow_factory():
                session_factory = DatabaseConnection.get_session_factory()
                session = session_factory()
                return PostgresUnitOfWork(session)

            service = LogSyncService(redis_repo, uow_factory)
            count = await service.sync_logs()

            if count > 0:
                logger.info(f"Scheduled log sync completed. Synced {count} logs.")

        except asyncio.CancelledError:
            logger.info("Log sync task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in background log sync: {e}")
            # Wait a bit before continuing to avoid tight loop on persistent error
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")

    try:
        redis_client = await RedisConnection.get_client()
        await redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise

    try:
        engine = DatabaseConnection.get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise

    # Start background tasks
    log_sync_task = asyncio.create_task(run_background_log_sync())
    logger.info("Background log sync task started")

    yield

    logger.info("Shutting down application...")

    # Cancel background tasks
    log_sync_task.cancel()
    try:
        await log_sync_task
    except asyncio.CancelledError:
        logger.info("Background log sync task stopped")

    try:
        await RedisConnection.close_pool()
        logger.info("Redis connection pool closed")
    except Exception as e:
        logger.error(f"Error closing Redis pool: {e}")

    try:
        await DatabaseConnection.close()
        logger.info("PostgreSQL connection closed")
    except Exception as e:
        logger.error(f"Error closing PostgreSQL connection: {e}")


app = FastAPI(
    title="Authentication Service - Session Management",
    description="Session management microservice with Redis (hot storage) and PostgreSQL (audit)",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session_router)
app.include_router(otp_router)
app.include_router(registration_router)
app.include_router(login_router)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your access token (active_token from login response)"
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/health")
async def healthCheck():
    return {
        "status": "healthy",
        "service": "authentication-session-service"
    }


@app.get("/")
async def root():
    return {
        "message": "Authentication Service API",
        "version": "1.0.0",
        "docs": "/docs"
    }
