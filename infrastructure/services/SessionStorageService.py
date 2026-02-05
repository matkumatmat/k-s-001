from __future__ import annotations
import logging
from datetime import datetime, UTC
from typing import TYPE_CHECKING
from domain.client.DeviceFingerprintVO import DeviceFingerprintVO
from domain.client.UserSessionFactory import UserSessionFactory

if TYPE_CHECKING:
    from domain.client.UserMetadataDomain import UserMetadataDomain
    from domain.client.UserSessionDomain import UserSessionDomain
    from infrastructure.persistence.redis.RedisSessionRepository import RedisSessionRepository
    from uuid import UUID
    from fastapi import BackgroundTasks
    
logger = logging.getLogger(__name__)


class SessionStorageService:

    def __init__(
        self,
        redis_repo: RedisSessionRepository,
        uow_factory: callable
    ):
        self.redis_repo = redis_repo
        self.uow_factory = uow_factory

    async def create_session(
        self,
        user_id: UUID,
        metadata: UserMetadataDomain,
        background_tasks: BackgroundTasks,
        session_duration_days: int = 30
    ) -> UserSessionDomain:
        session = UserSessionFactory.create_new_session(
            user_id=user_id,
            metadata=metadata,
            session_duration_days=session_duration_days
        )

        await self.redis_repo.create(session)

        background_tasks.add_task(
            self._sync_to_postgres,
            session,
            operation="create"
        )

        return session

    async def get_session_by_id(self, sid: UUID) -> UserSessionDomain | None:
        session = await self.redis_repo.get_by_id(sid)
        if session:
            return session

        async with await self.uow_factory() as uow:
            session = await uow.sessions.get_by_id(sid)
            if session:
                await self._warm_redis_cache(session)
            return session

    async def get_session_by_token(self, active_token: str) -> UserSessionDomain | None:
        session = await self.redis_repo.get_by_active_token(active_token)
        if session:
            return session

        async with await self.uow_factory() as uow:
            session = await uow.sessions.get_by_active_token(active_token)
            if session:
                await self._warm_redis_cache(session)
            return session

    async def validate_session(
        self,
        active_token: str,
        incoming_metadata: UserMetadataDomain
    ) -> UserSessionDomain | None:
        session = await self.get_session_by_token(active_token)
        if session is None:
            return None

        incoming_fingerprint = DeviceFingerprintVO.from_metadata(incoming_metadata)
        current_time = datetime.now(UTC)

        if not session.is_valid_session(current_time, incoming_fingerprint):
            return None

        return session

    async def refresh_session(
        self,
        refresh_token: str,
        background_tasks: BackgroundTasks
    ) -> UserSessionDomain | None:
        session = await self.redis_repo.get_by_refresh_token(refresh_token)
        if session is None:
            async with await self.uow_factory() as uow:
                session = await uow.sessions.get_by_refresh_token(refresh_token)

        if session is None:
            return None

        current_time = datetime.now(UTC)
        if not session.can_refresh(current_time):
            return None

        session.regenerate_tokens()

        await self.redis_repo.update(session)

        background_tasks.add_task(
            self._sync_to_postgres,
            session,
            operation="update"
        )

        return session

    async def revoke_session(
        self,
        sid: UUID,
        background_tasks: BackgroundTasks
    ) -> bool:
        deleted = await self.redis_repo.delete(sid)

        background_tasks.add_task(
            self._sync_to_postgres_delete,
            sid
        )

        return deleted

    async def revoke_all_user_sessions(
        self,
        user_id: UUID,
        background_tasks: BackgroundTasks
    ) -> int:
        count = await self.redis_repo.delete_all_by_user(user_id)

        background_tasks.add_task(
            self._sync_to_postgres_delete_all,
            user_id
        )

        return count

    async def _warm_redis_cache(self, session: UserSessionDomain) -> None:
        try:
            current_time = datetime.now(UTC)
            if session.is_active_session(current_time):
                await self.redis_repo.create(session)
        except Exception as e:
            logger.warning(f"Failed to warm Redis cache for session {session.sid}: {e}")

    async def _sync_to_postgres(
        self,
        session: UserSessionDomain,
        operation: str,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> None:
        try:
            async with await self.uow_factory() as uow:
                if operation == "create":
                    await uow.sessions.create(session)
                elif operation == "update":
                    await uow.sessions.update(session)
                await uow.commit()
                logger.info(f"Successfully synced session {session.sid} to PostgreSQL ({operation})")
        except Exception as e:
            logger.error(f"Failed to sync session {session.sid} to PostgreSQL ({operation}): {e}")
            if retry_count < max_retries:
                logger.info(f"Retrying sync for session {session.sid} (attempt {retry_count + 1}/{max_retries})")
                await self._sync_to_postgres(session, operation, retry_count + 1, max_retries)
            else:
                logger.error(f"Max retries exceeded for session {session.sid} sync to PostgreSQL")

    async def _sync_to_postgres_delete(
        self,
        sid: UUID,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> None:
        try:
            async with await self.uow_factory() as uow:
                await uow.sessions.delete(sid)
                await uow.commit()
                logger.info(f"Successfully soft-deleted session {sid} in PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to delete session {sid} in PostgreSQL: {e}")
            if retry_count < max_retries:
                logger.info(f"Retrying delete for session {sid} (attempt {retry_count + 1}/{max_retries})")
                await self._sync_to_postgres_delete(sid, retry_count + 1, max_retries)
            else:
                logger.error(f"Max retries exceeded for session {sid} delete in PostgreSQL")

    async def _sync_to_postgres_delete_all(
        self,
        user_id: UUID,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> None:
        try:
            async with await self.uow_factory() as uow:
                await uow.sessions.delete_all_by_user(user_id)
                await uow.commit()
                logger.info(f"Successfully soft-deleted all sessions for user {user_id} in PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to delete all sessions for user {user_id} in PostgreSQL: {e}")
            if retry_count < max_retries:
                logger.info(f"Retrying delete all for user {user_id} (attempt {retry_count + 1}/{max_retries})")
                await self._sync_to_postgres_delete_all(user_id, retry_count + 1, max_retries)
            else:
                logger.error(f"Max retries exceeded for user {user_id} delete all sessions in PostgreSQL")
