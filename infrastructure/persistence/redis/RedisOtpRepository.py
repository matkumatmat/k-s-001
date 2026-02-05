from __future__ import annotations
import json
from datetime import datetime
from uuid import UUID
from domain.management.IOtpRepository import IOtpRepository
from domain.management.OtpAuthenticationFactory import OtpAuthenticationFactory
from domain.management.ValueObject import AuthenticationOtpPurpose, AuthenticationProvider
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.management.OtpAuthenticationDomain import ManagementOtpDomain
    from redis.asyncio import Redis


class RedisOtpRepository(IOtpRepository):

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def _otpKey(self, sid: UUID) -> str:
        return f"otp:{sid}"

    def _otpCodeTargetKey(self, otp_code: str, delivery_target: str) -> str:
        return f"otp:code:{otp_code}:target:{delivery_target}"

    def _otpTargetKey(self, delivery_target: str) -> str:
        return f"otp:target:{delivery_target}"

    def _serialize(self, otp: ManagementOtpDomain) -> str:
        data = {
            "sid": str(otp.sid),
            "otp_code": otp.otp_code,
            "otp_url": otp.otp_url,
            "delivery_target": otp.delivery_target,
            "delivery_method": otp.delivery_method.value,
            "purpose": otp.purpose.value,
            "expired_at": otp.expired_at.isoformat(),
            "merchant_id": str(otp.merchant_id),
            "used": otp.used,
            "used_at": otp.used_at.isoformat() if otp.used_at else None,
            "created_at": otp.created_at.isoformat(),
            "updated_at": otp.updated_at.isoformat(),
            "user_id": str(otp.user_id) if otp.user_id else None,
            "identifier": otp.identifier,
            "behaviour_logs": str(otp.behaviour_logs) if otp.behaviour_logs else None,
            "expiry_seconds": otp.expiry_seconds,
            "code_len": otp.code_len,
            "max_retries": otp.max_retries
        }
        return json.dumps(data)

    def _deserialize(self, data: str) -> ManagementOtpDomain:
        obj = json.loads(data)
        return OtpAuthenticationFactory.createFromPersistence(
            sid=UUID(obj["sid"]),
            otp_code=obj["otp_code"],
            otp_url=obj["otp_url"],
            delivery_target=obj["delivery_target"],
            delivery_method=AuthenticationProvider(obj["delivery_method"]),
            purpose=AuthenticationOtpPurpose(obj["purpose"]),
            expired_at=datetime.fromisoformat(obj["expired_at"]),
            merchant_id=UUID(obj["merchant_id"]),
            used=obj["used"],
            used_at=datetime.fromisoformat(obj["used_at"]) if obj["used_at"] else None,
            created_at=datetime.fromisoformat(obj["created_at"]),
            updated_at=datetime.fromisoformat(obj["updated_at"]),
            user_id=UUID(obj["user_id"]) if obj["user_id"] else None,
            identifier=obj["identifier"],
            behaviour_logs=UUID(obj["behaviour_logs"]) if obj["behaviour_logs"] else None,
            expiry_seconds=obj["expiry_seconds"],
            code_len=obj["code_len"],
            max_retries=obj["max_retries"]
        )

    async def create(self, otp: ManagementOtpDomain) -> ManagementOtpDomain:
        ttl = otp.expiry_seconds
        if ttl <= 0:
            raise ValueError("Cannot create OTP with non-positive TTL")

        serialized = self._serialize(otp)
        otp_key = self._otpKey(otp.sid)
        code_target_key = self._otpCodeTargetKey(otp.otp_code, otp.delivery_target)
        target_key = self._otpTargetKey(otp.delivery_target)

        pipe = self.redis.pipeline()
        pipe.setex(otp_key, ttl, serialized)
        pipe.setex(code_target_key, ttl, str(otp.sid))
        pipe.sadd(target_key, str(otp.sid))
        pipe.expire(target_key, ttl)
        await pipe.execute()

        return otp

    async def getById(self, sid: UUID) -> ManagementOtpDomain | None:
        key = self._otpKey(sid)
        data = await self.redis.get(key)
        if data is None:
            return None
        return self._deserialize(data)

    async def getByCodeAndTarget(self, otp_code: str, delivery_target: str) -> ManagementOtpDomain | None:
        code_target_key = self._otpCodeTargetKey(otp_code, delivery_target)
        sid_str = await self.redis.get(code_target_key)
        if sid_str is None:
            return None
        return await self.getById(UUID(sid_str))

    async def getByTarget(self, delivery_target: str) -> list[ManagementOtpDomain]:
        target_key = self._otpTargetKey(delivery_target)
        otp_ids = await self.redis.smembers(target_key)

        if not otp_ids:
            return []

        otps = []
        for sid_str in otp_ids:
            otp = await self.getById(UUID(sid_str))
            if otp:
                otps.append(otp)
        return otps

    async def getByUserIdAndPurpose(self, user_id: UUID, purpose: AuthenticationOtpPurpose) -> list[ManagementOtpDomain]:
        keys = await self.redis.keys("otp:*")
        otps = []
        for key in keys:
            data = await self.redis.get(key)
            if data:
                otp = self._deserialize(data)
                if otp.user_id == user_id and otp.purpose == purpose:
                    otps.append(otp)
        return otps

    async def update(self, otp: ManagementOtpDomain) -> ManagementOtpDomain:
        existing = await self.getById(otp.sid)
        if existing is None:
            raise ValueError(f"OTP {otp.sid} not found")

        await self.delete(otp.sid)
        return await self.create(otp)

    async def delete(self, sid: UUID) -> bool:
        otp = await self.getById(sid)
        if otp is None:
            return False

        otp_key = self._otpKey(sid)
        code_target_key = self._otpCodeTargetKey(otp.otp_code, otp.delivery_target)
        target_key = self._otpTargetKey(otp.delivery_target)

        pipe = self.redis.pipeline()
        pipe.delete(otp_key)
        pipe.delete(code_target_key)
        pipe.srem(target_key, str(sid))
        await pipe.execute()

        return True

    async def exists(self, sid: UUID) -> bool:
        key = self._otpKey(sid)
        return await self.redis.exists(key) > 0
