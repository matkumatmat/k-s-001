from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Any, Dict, Optional
from domain.logging.LogType import LogType

@dataclass(frozen=True)
class LogEntry:
    id: UUID
    log_type: LogType
    action: str
    message: str
    metadata: Dict[str, Any]
    created_at: datetime
    user_id: Optional[UUID] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "log_type": self.log_type.value,
            "action": self.action,
            "message": self.message,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "user_id": str(self.user_id) if self.user_id else None
        }
