import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from domain.logging.LogFactory import LogFactory
from domain.logging.LogType import LogType
from infrastructure.persistence.redis.RedisLogRepository import RedisLogRepository
from infrastructure.services.LogSyncService import LogSyncService

def test_log_factory_creates_correct_entry():
    user_id = uuid4()
    log = LogFactory.create_user_behavior_log(
        user_id=user_id,
        action="CLICK",
        message="User clicked button",
        metadata={"button_id": "submit"}
    )

    assert log.log_type == LogType.USER_BEHAVIOR
    assert log.action == "CLICK"
    assert log.message == "User clicked button"
    assert log.metadata["button_id"] == "submit"
    assert log.user_id == user_id
    assert isinstance(log.created_at, datetime)

def test_redis_log_repository_serialization():
    async def run_test():
        # Mock Redis
        mock_redis = AsyncMock()
        repo = RedisLogRepository(mock_redis)

        log = LogFactory.create_system_log(
            action="STARTUP",
            message="System started"
        )

        # Test Serialize
        serialized = repo._serialize(log)
        assert "STARTUP" in serialized
        assert "System started" in serialized

        # Test Deserialize
        deserialized = repo._deserialize(serialized)
        assert deserialized.id == log.id
        assert deserialized.action == log.action
        assert deserialized.message == log.message
        assert deserialized.created_at == log.created_at

    asyncio.run(run_test())

def test_log_sync_service():
    async def run_test():
        # Mock Redis Repo
        mock_redis_repo = AsyncMock()
        log1 = LogFactory.create_system_log("TEST1", "Msg1")
        log2 = LogFactory.create_system_log("TEST2", "Msg2")

        # Setup pop_batch to return logs once, then empty
        mock_redis_repo.pop_batch.side_effect = [[log1, log2], []]

        # Mock UoW
        mock_uow = AsyncMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow.__aexit__.return_value = None

        # Mock UoW Factory
        async def mock_uow_factory():
            return mock_uow

        service = LogSyncService(mock_redis_repo, mock_uow_factory)

        count = await service.sync_logs(batch_size=10)

        assert count == 2
        mock_uow.logs.bulk_create.assert_called_once()
        saved_logs = mock_uow.logs.bulk_create.call_args[0][0]
        assert len(saved_logs) == 2
        assert saved_logs[0].action == "TEST1"
        mock_uow.commit.assert_called_once()

    asyncio.run(run_test())
