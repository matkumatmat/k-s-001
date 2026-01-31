from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime, timedelta
import secrets
from domain.client.UserMetadataDomain import UserMetadataDomain
from domain.client.DeviceFingerprintVO import DeviceFingerprintVO


@dataclass
class UserSessionDomain:
    sid : UUID
    user_id : UUID
    active : datetime
    expiry : datetime
    metadata : UserMetadataDomain
    device_fingerprint : DeviceFingerprintVO
    active_token : str = field(default_factory=lambda: secrets.token_urlsafe(32))
    refresh_token : str = field(default_factory=lambda: secrets.token_urlsafe(32))

    def __post_init__(self):
        if self.expiry <= self.active:
            raise ValueError("Session expiry must be after active timestamp")

    def is_expired(self, current_time: datetime) -> bool:
        return current_time >= self.expiry

    def is_active_session(self, current_time: datetime) -> bool:
        return not self.is_expired(current_time)

    def validate_fingerprint(self, incoming_fingerprint: DeviceFingerprintVO) -> bool:
        return self.device_fingerprint.matches(incoming_fingerprint)

    def regenerate_tokens(self) -> None:
        self.active_token = secrets.token_urlsafe(32)
        self.refresh_token = secrets.token_urlsafe(32)

    def regenerate_active_token(self) -> None:
        self.active_token = secrets.token_urlsafe(32)

    def extend_session(self, extension_duration: timedelta) -> None:
        self.expiry = self.expiry + extension_duration

    def get_client_response(self) -> dict[str, str]:
        return {
            "active_token": self.active_token,
            "refresh_token": self.refresh_token,
            "device_fingerprint": self.device_fingerprint.encoded,
            "expires_at": self.expiry.isoformat()
        }

    def verify_active_token(self, token: str) -> bool:
        return self.active_token == token

    def verify_refresh_token(self, token: str) -> bool:
        return self.refresh_token == token

    def can_refresh(self, current_time: datetime) -> bool:
        return not self.is_expired(current_time)

    def ttl_seconds(self, current_time: datetime) -> int:
        if self.is_expired(current_time):
            return 0
        delta = self.expiry - current_time
        return int(delta.total_seconds())

    def is_valid_session(self, current_time: datetime, incoming_fingerprint: DeviceFingerprintVO) -> bool:
        return (
            self.is_active_session(current_time) and
            self.validate_fingerprint(incoming_fingerprint)
        )


# if __name__ == "__main__":
#     import traceback
#     import uuid
#     from domain.client.UserMetadataDomain import UserMetadataDomain
#     from domain.client.DeviceFingerprintVO import DeviceFingerprintVO

#     try:
#         uid = uuid.uuid7() if hasattr(uuid, 'uuid7') else uuid.uuid4()
#     except:
#         uid = uuid.uuid4()

#     now = datetime.now()
#     future_time = now + timedelta(hours=1)
#     past_time = now - timedelta(hours=1)

#     metadata = UserMetadataDomain(
#         user_agent="Mozilla/5.0 (iPhone)",
#         devices_width=375,
#         devices_length=667,
#         ip_address="192.168.1.1",
#         region="ID",
#         lang="id-ID"
#     )
#     fingerprint = DeviceFingerprintVO.from_metadata(metadata)

#     print("=== START TESTING ===")

#     print("\n[TEST 1] Session Creation with Auto Token Generation")
#     try:
#         session = UserSessionDomain(
#             sid=uid,
#             user_id=uuid.uuid4(),
#             active=now,
#             expiry=future_time,
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         print(f"Session created with SID: {session.sid}")
#         print(f"Active token generated: {session.active_token[:20]}...")
#         print(f"Refresh token generated: {session.refresh_token[:20]}...")

#         assert len(session.active_token) > 0
#         assert len(session.refresh_token) > 0
#         assert session.active_token != session.refresh_token
#         print(">> TEST 1 PASSED")
#     except Exception as e:
#         print(f">> TEST 1 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 2] Validation Error (Expiry Before Active)")
#     try:
#         print("Attempting to create session with expiry <= active...")
#         invalid_session = UserSessionDomain(
#             sid=uid,
#             user_id=uuid.uuid4(),
#             active=future_time,
#             expiry=now,
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         print(">> TEST 2 FAILED (Should raise ValueError)")
#     except ValueError as e:
#         print(f"Caught expected error: {e}")
#         print(">> TEST 2 PASSED")
#     except Exception as e:
#         print(f">> TEST 2 FAILED (Wrong error type): {e}")

#     print("\n[TEST 3] Session Expiry Logic (Not Expired)")
#     try:
#         session = UserSessionDomain(
#             sid=uuid.uuid4(),
#             user_id=uuid.uuid4(),
#             active=now,
#             expiry=future_time,
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         print(f"Is expired (Expected False): {session.is_expired(now)}")
#         print(f"Is active session (Expected True): {session.is_active_session(now)}")

#         assert session.is_expired(now) is False
#         assert session.is_active_session(now) is True
#         print(">> TEST 3 PASSED")
#     except Exception as e:
#         print(f">> TEST 3 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 4] Session Expiry Logic (Expired)")
#     try:
#         expired_session = UserSessionDomain(
#             sid=uuid.uuid4(),
#             user_id=uuid.uuid4(),
#             active=past_time,
#             expiry=now - timedelta(minutes=1),
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         print(f"Is expired (Expected True): {expired_session.is_expired(now)}")
#         print(f"Is active session (Expected False): {expired_session.is_active_session(now)}")

#         assert expired_session.is_expired(now) is True
#         assert expired_session.is_active_session(now) is False
#         print(">> TEST 4 PASSED")
#     except Exception as e:
#         print(f">> TEST 4 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 5] Fingerprint Validation (Matching)")
#     try:
#         session = UserSessionDomain(
#             sid=uuid.uuid4(),
#             user_id=uuid.uuid4(),
#             active=now,
#             expiry=future_time,
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         incoming_fp = DeviceFingerprintVO.from_metadata(metadata)
#         print(f"Fingerprint matches (Expected True): {session.validate_fingerprint(incoming_fp)}")

#         assert session.validate_fingerprint(incoming_fp) is True
#         print(">> TEST 5 PASSED")
#     except Exception as e:
#         print(f">> TEST 5 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 6] Fingerprint Validation (Not Matching)")
#     try:
#         session = UserSessionDomain(
#             sid=uuid.uuid4(),
#             user_id=uuid.uuid4(),
#             active=now,
#             expiry=future_time,
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         different_metadata = UserMetadataDomain(
#             user_agent="Different User Agent",
#             devices_width=1920,
#             devices_length=1080,
#             ip_address="10.0.0.1",
#             region="US",
#             lang="en-US"
#         )
#         different_fp = DeviceFingerprintVO.from_metadata(different_metadata)
#         print(f"Fingerprint matches (Expected False): {session.validate_fingerprint(different_fp)}")

#         assert session.validate_fingerprint(different_fp) is False
#         print(">> TEST 6 PASSED")
#     except Exception as e:
#         print(f">> TEST 6 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 7] Token Regeneration (Both Tokens)")
#     try:
#         session = UserSessionDomain(
#             sid=uuid.uuid4(),
#             user_id=uuid.uuid4(),
#             active=now,
#             expiry=future_time,
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         old_active = session.active_token
#         old_refresh = session.refresh_token

#         session.regenerate_tokens()

#         print(f"Active token changed (Expected True): {session.active_token != old_active}")
#         print(f"Refresh token changed (Expected True): {session.refresh_token != old_refresh}")

#         assert session.active_token != old_active
#         assert session.refresh_token != old_refresh
#         print(">> TEST 7 PASSED")
#     except Exception as e:
#         print(f">> TEST 7 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 8] Token Regeneration (Active Only)")
#     try:
#         session = UserSessionDomain(
#             sid=uuid.uuid4(),
#             user_id=uuid.uuid4(),
#             active=now,
#             expiry=future_time,
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         old_active = session.active_token
#         old_refresh = session.refresh_token

#         session.regenerate_active_token()

#         print(f"Active token changed (Expected True): {session.active_token != old_active}")
#         print(f"Refresh token unchanged (Expected True): {session.refresh_token == old_refresh}")

#         assert session.active_token != old_active
#         assert session.refresh_token == old_refresh
#         print(">> TEST 8 PASSED")
#     except Exception as e:
#         print(f">> TEST 8 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 9] Session Extension")
#     try:
#         session = UserSessionDomain(
#             sid=uuid.uuid4(),
#             user_id=uuid.uuid4(),
#             active=now,
#             expiry=future_time,
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         old_expiry = session.expiry
#         extension = timedelta(days=7)

#         session.extend_session(extension)

#         print(f"Old expiry: {old_expiry}")
#         print(f"New expiry: {session.expiry}")
#         print(f"Extended correctly (Expected True): {session.expiry == old_expiry + extension}")

#         assert session.expiry == old_expiry + extension
#         print(">> TEST 9 PASSED")
#     except Exception as e:
#         print(f">> TEST 9 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 10] Client Response Format")
#     try:
#         session = UserSessionDomain(
#             sid=uuid.uuid4(),
#             user_id=uuid.uuid4(),
#             active=now,
#             expiry=future_time,
#             metadata=metadata,
#             device_fingerprint=fingerprint
#         )
#         response = session.get_client_response()

#         print(f"Response keys: {list(response.keys())}")
#         print(f"Has active_token (Expected True): {'active_token' in response}")
#         print(f"Has refresh_token (Expected True): {'refresh_token' in response}")
#         print(f"Has device_fingerprint (Expected True): {'device_fingerprint' in response}")
#         print(f"Has expires_at (Expected True): {'expires_at' in response}")

#         assert "active_token" in response
#         assert "refresh_token" in response
#         assert "device_fingerprint" in response
#         assert "expires_at" in response
#         assert response["active_token"] == session.active_token
#         assert response["refresh_token"] == session.refresh_token
#         assert response["device_fingerprint"] == fingerprint.encoded
#         print(">> TEST 10 PASSED")
#     except Exception as e:
#         print(f">> TEST 10 FAILED: {e}")
#         traceback.print_exc()

#     print("\n=== END TESTING ===")

