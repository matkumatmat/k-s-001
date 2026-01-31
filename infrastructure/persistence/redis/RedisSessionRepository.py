from __future__ import annotations
import json
from datetime import datetime, timezone
from uuid import UUID
from redis.asyncio import Redis
from domain.client.ISessionRepository import ISessionRepository
from domain.client.UserSessionDomain import UserSessionDomain
from domain.client.UserMetadataDomain import UserMetadataDomain
from domain.client.DeviceFingerprintVO import DeviceFingerprintVO
from domain.client.UserSessionFactory import UserSessionFactory


class RedisSessionRepository(ISessionRepository):

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def _session_key(self, sid: UUID) -> str:
        return f"session:{sid}"

    def _user_sessions_key(self, user_id: UUID) -> str:
        return f"user_sessions:{user_id}"

    def _active_token_key(self, token: str) -> str:
        return f"session:token:active:{token}"

    def _refresh_token_key(self, token: str) -> str:
        return f"session:token:refresh:{token}"

    def _serialize(self, session: UserSessionDomain) -> str:
        data = {
            "sid": str(session.sid),
            "user_id": str(session.user_id),
            "active": session.active.isoformat(),
            "expiry": session.expiry.isoformat(),
            "active_token": session.active_token,
            "refresh_token": session.refresh_token,
            "metadata": {
                "user_agent": session.metadata.user_agent,
                "devices_width": session.metadata.devices_width,
                "devices_length": session.metadata.devices_length,
                "ip_address": session.metadata.ip_address,
                "region": session.metadata.region,
                "lang": session.metadata.lang
            },
            "device_fingerprint": session.device_fingerprint.encoded
        }
        return json.dumps(data)

    def _deserialize(self, data: str) -> UserSessionDomain:
        obj = json.loads(data)
        metadata = UserMetadataDomain(
            user_agent=obj["metadata"]["user_agent"],
            devices_width=obj["metadata"]["devices_width"],
            devices_length=obj["metadata"]["devices_length"],
            ip_address=obj["metadata"]["ip_address"],
            region=obj["metadata"]["region"],
            lang=obj["metadata"]["lang"]
        )
        fingerprint = DeviceFingerprintVO.from_encoded(obj["device_fingerprint"])

        return UserSessionFactory.create_from_persistence(
            sid=UUID(obj["sid"]),
            user_id=UUID(obj["user_id"]),
            active=datetime.fromisoformat(obj["active"]),
            expiry=datetime.fromisoformat(obj["expiry"]),
            metadata=metadata,
            device_fingerprint=fingerprint,
            active_token=obj["active_token"],
            refresh_token=obj["refresh_token"]
        )

    async def create(self, session: UserSessionDomain) -> UserSessionDomain:
        ttl = session.ttl_seconds(datetime.now(timezone.utc))
        if ttl <= 0:
            raise ValueError("Cannot create expired session")

        serialized = self._serialize(session)
        session_key = self._session_key(session.sid)
        user_sessions_key = self._user_sessions_key(session.user_id)
        active_token_key = self._active_token_key(session.active_token)
        refresh_token_key = self._refresh_token_key(session.refresh_token)

        pipe = self.redis.pipeline()
        pipe.setex(session_key, ttl, serialized)
        pipe.sadd(user_sessions_key, str(session.sid))
        pipe.expire(user_sessions_key, ttl)
        pipe.setex(active_token_key, ttl, str(session.sid))
        pipe.setex(refresh_token_key, ttl, str(session.sid))
        await pipe.execute()

        return session

    async def get_by_id(self, sid: UUID) -> UserSessionDomain | None:
        key = self._session_key(sid)
        data = await self.redis.get(key)
        if data is None:
            return None
        return self._deserialize(data)

    async def get_by_user_id(self, user_id: UUID) -> list[UserSessionDomain]:
        user_sessions_key = self._user_sessions_key(user_id)
        session_ids = await self.redis.smembers(user_sessions_key)

        if not session_ids:
            return []

        sessions = []
        for sid_str in session_ids:
            session = await self.get_by_id(UUID(sid_str))
            if session:
                sessions.append(session)
        return sessions

    async def get_by_active_token(self, active_token: str) -> UserSessionDomain | None:
        token_key = self._active_token_key(active_token)
        sid_str = await self.redis.get(token_key)
        if sid_str is None:
            return None
        return await self.get_by_id(UUID(sid_str))

    async def get_by_refresh_token(self, refresh_token: str) -> UserSessionDomain | None:
        token_key = self._refresh_token_key(refresh_token)
        sid_str = await self.redis.get(token_key)
        if sid_str is None:
            return None
        return await self.get_by_id(UUID(sid_str))

    async def update(self, session: UserSessionDomain) -> UserSessionDomain:
        existing = await self.get_by_id(session.sid)
        if existing is None:
            raise ValueError(f"Session {session.sid} not found")

        await self.delete(session.sid)
        return await self.create(session)

    async def delete(self, sid: UUID) -> bool:
        session = await self.get_by_id(sid)
        if session is None:
            return False

        session_key = self._session_key(sid)
        user_sessions_key = self._user_sessions_key(session.user_id)
        active_token_key = self._active_token_key(session.active_token)
        refresh_token_key = self._refresh_token_key(session.refresh_token)

        pipe = self.redis.pipeline()
        pipe.delete(session_key)
        pipe.srem(user_sessions_key, str(sid))
        pipe.delete(active_token_key)
        pipe.delete(refresh_token_key)
        await pipe.execute()

        return True

    async def delete_all_by_user(self, user_id: UUID) -> int:
        sessions = await self.get_by_user_id(user_id)
        count = 0
        for session in sessions:
            deleted = await self.delete(session.sid)
            if deleted:
                count += 1
        return count

    async def exists(self, sid: UUID) -> bool:
        key = self._session_key(sid)
        return await self.redis.exists(key) > 0
