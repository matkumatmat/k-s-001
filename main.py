from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from application.SessionApplication.router.SessionRouter import router as session_router
from application.OtpApplication.router.OtpRouter import router as otp_router
from application.RegistrationApplication.router.RegistrationRouter import router as registration_router
from application.LoginApplication.router.LoginRouter import router as login_router
from infrastructure.persistence.redis.connection import RedisConnection
from infrastructure.persistence.postgresql.connection import DatabaseConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    yield

    logger.info("Shutting down application...")

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
    lifespan=lifespan
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
