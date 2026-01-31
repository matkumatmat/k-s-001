from __future__ import annotations
from datetime import datetime, UTC
from uuid import uuid4, UUID
from typing import Any, Dict, Optional
from domain.logging.LogEntry import LogEntry
from domain.logging.LogType import LogType

class LogFactory:
    @staticmethod
    def _create(
        log_type: LogType,
        action: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[UUID] = None
    ) -> LogEntry:
        return LogEntry(
            id=uuid4(),
            log_type=log_type,
            action=action,
            message=message,
            metadata=metadata or {},
            created_at=datetime.now(UTC),
            user_id=user_id
        )

    @classmethod
    def create_system_log(
        cls,
        action: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogEntry:
        return cls._create(LogType.SYSTEM, action, message, metadata)

    @classmethod
    def create_user_behavior_log(
        cls,
        user_id: UUID,
        action: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogEntry:
        return cls._create(LogType.USER_BEHAVIOR, action, message, metadata, user_id)

    @classmethod
    def create_session_log(
        cls,
        user_id: Optional[UUID],
        action: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogEntry:
        return cls._create(LogType.SESSION, action, message, metadata, user_id)
