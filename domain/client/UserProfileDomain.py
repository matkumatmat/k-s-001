from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import secrets
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID
    from domain.management.ValueObject import AuthenticationProvider, AuthenticationRole
@dataclass
class UserDomain:
    sid: UUID
    username: str
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    address: str | None = None
    region: str | None = None
    register_geolocation : str | None = None
    metadata: dict | None = None
    primary_contact: AuthenticationProvider | None = None
    role: AuthenticationRole | None = None
    secret_name: str = field(default_factory=lambda: secrets.token_hex(4))
    active: bool = True
    actived_at: datetime | None = None
    verified: bool = False
    verified_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None
    deleted: bool = False
    deleted_at: datetime | None = None

    def __post_init__(self):
        self.username = self.username.strip()
        self.validate_username()
        self.validate_password()

    def __bool__(self):
            return self.active and self.verified

    def validate_username(self):
        if len(self.username) < 4:
            raise ValueError("Username too short (min 4 chars)")

    def validate_password(self):
        if len(self.password) < 6:
            raise ValueError("Password too short (min 6 chars)")
        
    def has_password(self) -> bool:
        return bool(self.password)
        
    def has_firstname(self) -> bool:
        return self.first_name is not None
    
    def has_lastname(self) -> bool:
        return self.last_name is not None
    
    def full_name(self) -> str:
        parts = [name for name in (self.first_name, self.last_name) if name]
        return " ".join(parts) if parts else self.username
    
    def has_email(self) -> bool:
        return bool(self.email)

    def has_phone(self) -> bool:
        return self.phone is not None

    def has_region(self) -> bool:
        return self.region is not None

    def mark_active(self, activate_time: datetime):
        self.active = True
        self.actived_at = activate_time
        
    def mark_inactive(self, inactive_time: datetime):
        self.active = False
        self.updated_at = inactive_time

    def mark_verified(self, verified_time: datetime):
        self.verified = True
        self.verified_at = verified_time

    def mark_deleted(self, deleted_time: datetime):
        self.deleted = True
        self.deleted_at = deleted_time
        self.active = False

    def update_password(self, new_password: str):
        self.password = new_password

    def is_active(self) -> bool:
        return self.active
    
    def is_verified(self) -> bool:
        return self.verified

    def is_deleted(self) -> bool:
        return self.deleted
    
    def can_authenticate(self) -> bool:
        return self.is_active() and self.is_verified() and not self.is_deleted()

    def has_primary_contact(self) -> bool:
        return self.has_email() or self.has_phone()

    def can_add_auth_provider(self) -> bool:
        return self.has_email() or self.has_phone()

    def get_primary_contact(self) -> str | None:
        if self.has_email():
            return self.email
        if self.has_phone():
            return self.phone
        return None
    
    def supports_password_auth(self) -> bool:
        return (self.has_email() or self.has_phone()) and self.has_password()

    def confirm_email_update(self, new_email: str, verified_time: datetime) -> None:
        self.email = new_email
        self.updated_at = verified_time
        self.mark_verified(verified_time)

    def confirm_phone_update(self, new_phone: str, verified_time: datetime) -> None:
        self.phone = new_phone
        self.updated_at = verified_time

    def change_password(self, new_hashed_password: str, updated_time: datetime) -> None:
        self.password = new_hashed_password
        self.updated_at = updated_time

    def prepare_for_soft_delete(self, deletion_time: datetime) -> None:
        self.mark_deleted(deletion_time)
        self.mark_inactive(deletion_time)


# if __name__ == "__main__":
#     import uuid
#     from datetime import datetime, timezone

#     # Setup dummy data
#     now = datetime.now(timezone.utc)
#     uid = uuid.uuid7()

#     print("--- START TESTING ---")

#     # 1. TEST HAPPY PATH (User Valid)
#     print("\n[1] Testing Create Valid User")
#     try:
#         user = UserDomain(
#             sid=uid,
#             username="  admin_user  ", # Ada spasi untuk test strip()
#             email="admin@example.com",
#             password="securepassword123",
#             first_name="Admin",
#             last_name="System",
#             phone="08123456789"
#         )
#         print(f"User Created: {user.username} (Spasi hilang: {user.username == 'admin_user'})")
#         print(f"{user.sid}")
#         print(f"Secret Name Generated: {user.secret_name}")
#         print(f"Default Active: {user.is_active()}")
#         print(f"Default Verified: {user.is_verified()}")
#     except Exception as e:
#         print(f"FAILED: {e}")

#     # 2. TEST VALIDATION ERROR (Username Pendek)
#     print("\n[2] Testing Invalid Username (<4 chars)")
#     try:
#         UserDomain(uid, "abc", "mail", "pass123")
#         print("FAILED: Harusnya Error tapi lolos.")
#     except ValueError as e:
#         print(f"SUCCESS: Error tertangkap -> {e}")

#     # 3. TEST VALIDATION ERROR (Password Pendek)
#     print("\n[3] Testing Invalid Password (<6 chars)")
#     try:
#         UserDomain(uid, "validuser", "mail", "12345")
#         print("FAILED: Harusnya Error tapi lolos.")
#     except ValueError as e:
#         print(f"SUCCESS: Error tertangkap -> {e}")

#     # 4. TEST LOGIC FULL NAME
#     print("\n[4] Testing Full Name Logic")
#     print(f"Full (First+Last): '{user.full_name()}'")
    
#     user.last_name = None
#     print(f"Full (First Only): '{user.full_name()}'")
    
#     user.first_name = None
#     print(f"Full (None -> Username): '{user.full_name()}'")

#     # 5. TEST AUTHENTICATION FLOW
#     print("\n[5] Testing Auth Flow")
#     # Awal create belum verified
#     print(f"Can Auth (Belum Verify): {user.can_authenticate()} (Expected: False)")
    
#     # Verifikasi User
#     user.mark_verified(now)
#     print(f"Status Verified: {user.is_verified()}")
#     print(f"Can Auth (Verified): {user.can_authenticate()} (Expected: True)")

#     # Matikan User (Inactive)
#     user.mark_inactive(now)
#     print(f"Can Auth (Inactive): {user.can_authenticate()} (Expected: False)")

#     # Hidupkan lagi
#     user.mark_active(now)
#     print(f"Can Auth (Active Again): {user.can_authenticate()} (Expected: True)")

#     # 6. TEST DELETE (Soft Delete)
#     print("\n[6] Testing Soft Delete")
#     user.prepare_for_soft_delete(now)
#     print(f"Deleted Status: {user.is_deleted()}")
#     print(f"Active Status: {user.is_active()} (Expected: False)")
#     print(f"Can Auth: {user.can_authenticate()} (Expected: False)")

#     # 7. TEST UPDATES
#     print("\n[7] Testing Updates")
#     user.change_password("new_pass_hash", now)
#     print(f"Password Updated: {user.password == 'new_pass_hash'}")
    
#     user.confirm_email_update("new@mail.com", now)
#     print(f"Email Updated: {user.email}")
#     print(f"Verification Timestamp: {user.verified_at == now}")

#     print("\n--- END TESTING ---")
