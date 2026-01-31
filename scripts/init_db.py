import asyncio
import logging
from infrastructure.persistence.postgresql.connection import DatabaseConnection
from infrastructure.persistence.postgresql.models.SessionModel import Base
from infrastructure.persistence.postgresql.models.OtpModel import OtpModel
from infrastructure.persistence.postgresql.models.UserModel import UserModel
from infrastructure.persistence.postgresql.models.LogModel import LogModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    logger.info("Initializing database...")
    engine = DatabaseConnection.get_engine()

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully.")
    await DatabaseConnection.close()

if __name__ == "__main__":
    asyncio.run(init_db())
