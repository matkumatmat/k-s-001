from __future__ import annotations
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from infrastructure.persistence.postgresql.models.SessionModel import Base
from typing import TYPE_CHECKING


class UserModel(Base):
    __tablename__ = "users"

    sid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    register_geolocation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    metadata_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    primary_contact: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    secret_name: Mapped[str] = mapped_column(String(255), nullable=False)

    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    actived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"UserModel(sid={self.sid}, username={self.username})"
