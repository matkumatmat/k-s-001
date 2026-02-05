from infrastructure.persistence.postgresql.models.UserModel import UserModel
from domain.client.UserProfileDomain import UserDomain
from domain.management.ValueObject import AuthenticationProvider, AuthenticationRole

class UserMapper:
    @staticmethod
    def to_domain(model: UserModel) -> UserDomain:
        return UserDomain(
            sid=model.sid,
            username=model.username,
            email=model.email,
            password=model.password,
            first_name=model.first_name,
            last_name=model.last_name,
            phone=model.phone,
            address=model.address,
            region=model.region,
            register_geolocation=model.register_geolocation,
            metadata=model.metadata_info,
            primary_contact=AuthenticationProvider(model.primary_contact) if model.primary_contact else None,
            role=AuthenticationRole(model.role) if model.role else None,
            secret_name=model.secret_name,
            active=model.active,
            actived_at=model.actived_at,
            verified=model.verified,
            verified_at=model.verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted=model.deleted,
            deleted_at=model.deleted_at
        )

    @staticmethod
    def to_model(domain: UserDomain) -> UserModel:
        return UserModel(
            sid=domain.sid,
            username=domain.username,
            email=domain.email,
            password=domain.password,
            first_name=domain.first_name,
            last_name=domain.last_name,
            phone=domain.phone,
            address=domain.address,
            region=domain.region,
            register_geolocation=domain.register_geolocation,
            metadata_info=domain.metadata,
            primary_contact=domain.primary_contact.value if domain.primary_contact else None,
            role=domain.role.value if domain.role else None,
            secret_name=domain.secret_name,
            active=domain.active,
            actived_at=domain.actived_at,
            verified=domain.verified,
            verified_at=domain.verified_at,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            deleted=domain.deleted,
            deleted_at=domain.deleted_at
        )
