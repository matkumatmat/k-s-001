from __future__ import annotations
from datetime import datetime, timezone
from domain.management.OtpAuthenticationDomain import ManagementOtpDomain
from domain.management.OtpAuthenticationFactory import OtpAuthenticationFactory
from domain.management.ValueObject import AuthenticationOtpPurpose, AuthenticationProvider
from infrastructure.persistence.postgresql.models.OtpModel import OtpModel


class OtpMapper:

    @staticmethod
    def toModel(domain: ManagementOtpDomain) -> OtpModel:
        return OtpModel(
            sid=domain.sid,
            otp_code=domain.otp_code,
            otp_url=domain.otp_url,
            delivery_target=domain.delivery_target,
            delivery_method=domain.delivery_method.value,
            purpose=domain.purpose.value,
            expired_at=domain.expired_at,
            merchant_id=domain.merchant_id,
            used=domain.used,
            used_at=domain.used_at,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            user_id=domain.user_id,
            identifier=domain.identifier,
            behaviour_logs=domain.behaviour_logs,
            expiry_seconds=domain.expiry_seconds,
            code_len=domain.code_len,
            max_retries=domain.max_retries
        )

    @staticmethod
    def toDomain(model: OtpModel) -> ManagementOtpDomain:
        return OtpAuthenticationFactory.createFromPersistence(
            sid=model.sid,
            otp_code=model.otp_code,
            otp_url=model.otp_url,
            delivery_target=model.delivery_target,
            delivery_method=AuthenticationProvider(model.delivery_method),
            purpose=AuthenticationOtpPurpose(model.purpose),
            expired_at=model.expired_at,
            merchant_id=model.merchant_id,
            used=model.used,
            used_at=model.used_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            user_id=model.user_id,
            identifier=model.identifier,
            behaviour_logs=model.behaviour_logs,
            expiry_seconds=model.expiry_seconds,
            code_len=model.code_len,
            max_retries=model.max_retries
        )

    @staticmethod
    def updateModel(model: OtpModel, domain: ManagementOtpDomain) -> OtpModel:
        model.otp_code = domain.otp_code
        model.otp_url = domain.otp_url
        model.delivery_target = domain.delivery_target
        model.delivery_method = domain.delivery_method.value
        model.purpose = domain.purpose.value
        model.expired_at = domain.expired_at
        model.merchant_id = domain.merchant_id
        model.used = domain.used
        model.used_at = domain.used_at
        model.updated_at = datetime.now(timezone.utc)
        model.user_id = domain.user_id
        model.identifier = domain.identifier
        model.behaviour_logs = domain.behaviour_logs
        model.expiry_seconds = domain.expiry_seconds
        model.code_len = domain.code_len
        model.max_retries = domain.max_retries
        return model
