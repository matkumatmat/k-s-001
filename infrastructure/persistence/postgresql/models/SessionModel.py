from __future__ import annotations
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from typing import TYPE_CHECKING


class Base(DeclarativeBase):
    pass


class SessionModel(Base):
    __tablename__ = "user_sessions"

    sid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    active: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    active_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    device_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    metadata_user_agent: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    metadata_devices_width: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_devices_length: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_region: Mapped[str] = mapped_column(String(10), nullable=False)
    metadata_lang: Mapped[str] = mapped_column(String(10), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"SessionModel(sid={self.sid}, user_id={self.user_id})"
