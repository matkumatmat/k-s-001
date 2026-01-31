from __future__ import annotations
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from infrastructure.persistence.postgresql.models.SessionModel import Base


class OtpModel(Base):
    __tablename__ = "otp_authentications"

    sid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    otp_url: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_target: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    delivery_method: Mapped[str] = mapped_column(String(50), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    expired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    merchant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)

    used: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    behaviour_logs: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    expiry_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    code_len: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    def __repr__(self) -> str:
        return f"OtpModel(sid={self.sid}, target={self.delivery_target}, purpose={self.purpose})"
