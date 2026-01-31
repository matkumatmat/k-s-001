from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from domain.client.UserSessionDomain import UserSessionDomain
from domain.client.UserMetadataDomain import UserMetadataDomain
from domain.client.DeviceFingerprintVO import DeviceFingerprintVO
from domain.client.UserSessionFactory import UserSessionFactory
from infrastructure.persistence.postgresql.models.SessionModel import SessionModel


class SessionMapper:

    @staticmethod
    def to_model(domain: UserSessionDomain) -> SessionModel:
        return SessionModel(
            sid=domain.sid,
            user_id=domain.user_id,
            active=domain.active,
            expiry=domain.expiry,
            active_token=domain.active_token,
            refresh_token=domain.refresh_token,
            device_fingerprint=domain.device_fingerprint.encoded,
            metadata_user_agent=domain.metadata.user_agent,
            metadata_ip_address=domain.metadata.ip_address,
            metadata_devices_width=domain.metadata.devices_width,
            metadata_devices_length=domain.metadata.devices_length,
            metadata_region=domain.metadata.region,
            metadata_lang=domain.metadata.lang,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            deleted=False,
            deleted_at=None
        )

    @staticmethod
    def to_domain(model: SessionModel) -> UserSessionDomain:
        metadata = UserMetadataDomain(
            user_agent=model.metadata_user_agent,
            devices_width=model.metadata_devices_width,
            devices_length=model.metadata_devices_length,
            ip_address=model.metadata_ip_address,
            region=model.metadata_region,
            lang=model.metadata_lang
        )

        fingerprint = DeviceFingerprintVO.from_encoded(model.device_fingerprint)

        return UserSessionFactory.create_from_persistence(
            sid=model.sid,
            user_id=model.user_id,
            active=model.active,
            expiry=model.expiry,
            metadata=metadata,
            device_fingerprint=fingerprint,
            active_token=model.active_token,
            refresh_token=model.refresh_token
        )

    @staticmethod
    def update_model(model: SessionModel, domain: UserSessionDomain) -> SessionModel:
        model.active = domain.active
        model.expiry = domain.expiry
        model.active_token = domain.active_token
        model.refresh_token = domain.refresh_token
        model.device_fingerprint = domain.device_fingerprint.encoded
        model.metadata_user_agent = domain.metadata.user_agent
        model.metadata_ip_address = domain.metadata.ip_address
        model.metadata_devices_width = domain.metadata.devices_width
        model.metadata_devices_length = domain.metadata.devices_length
        model.metadata_region = domain.metadata.region
        model.metadata_lang = domain.metadata.lang
        model.updated_at = datetime.now(timezone.utc)
        return model
