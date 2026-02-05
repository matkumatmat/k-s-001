from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
import os
from dotenv import load_dotenv #type: ignore

from domain.management.ValueObject import AuthenticationOtpPurpose, AuthenticationProvider
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

load_dotenv()
URL_PREFIX = os.getenv("OTP_URL_PREFIX")
CODE_LENS = int(os.getenv("OTP_CODE_LEN", "6"))
OTP_MAX_RETRIES = int(os.getenv("OTP_MAX_RETRIES", "3"))
OTP_EXPIRES_SECONDS = int(os.getenv("OTP_EXPIRES_SECONDS", "300"))

@dataclass
class ManagementOtpDomain:
    sid : UUID
    otp_code : str
    otp_url : str
    delivery_target : str
    delivery_method : AuthenticationProvider
    purpose : AuthenticationOtpPurpose
    expired_at: datetime
    merchant_id : UUID
    used: bool | None = None
    used_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    user_id : UUID | None = None
    identifier: str | None = None
    behaviour_logs: UUID | None = None
    expiry_seconds: int = OTP_EXPIRES_SECONDS
    code_len : int = CODE_LENS
    max_retries: int = OTP_MAX_RETRIES

    def get_expiry_duration(self) -> timedelta:
        return timedelta(seconds=self.expiry_seconds)
    
    def is_expired(self, current_time: datetime | None = None) -> bool:
        if current_time is None:
            current_time = datetime.now(UTC)
        return current_time > self.expired_at
    
    def mark_used(self, current_time: datetime) -> None :
        self.used = True
        self.used_at = current_time

    def __bool__(self):
        return not self.is_expired() and not self.used
    
    def match_target(self, target:str) -> bool:
        return self.delivery_target == target
    
    def __getattr__(self, name:str):
        if name.startswith("is_"):
            enum_key = name[3:].upper()
        if enum_key in AuthenticationOtpPurpose.__members__:
            return self.purpose == AuthenticationOtpPurpose[enum_key]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        # how to use : otp.is_login  -> True

    def gen_otp_url(self, prefix: str) -> str:
        return prefix.format(code=self.otp_code)
    
    def otp_merchant(self, merchant:UUID):
        return self.merchant_id

# # --- COMPREHENSIVE TESTING BLOCK ---
# if __name__ == "__main__":
#     import traceback
#     import uuid
    
#     # Setup Waktu
#     now = datetime.now(timezone.utc)
#     future_time = now + timedelta(minutes=5)
#     past_time = now - timedelta(minutes=5)
    
#     # Setup UUID (Safe fallback for Python versions without uuid7)
#     try:
#         uid = uuid.uuid7() if hasattr(uuid, 'uuid7') else uuid.uuid4()
#     except:
#         uid = uuid.uuid4()

#     print("=== START TESTING ===")

#     # ---------------------------------------------------------
#     # TEST 1: HAPPY PATH (Valid Object Creation & Dynamic Logic)
#     # ---------------------------------------------------------
#     print("\n[TEST 1] Initialization & Dynamic Attributes")
#     try:
#         otp = ManagementOtpDomain(
#             sid=uid,
#             otp_code="123456",
#             otp_url="https://auth.com/verify",
#             delivery_target="user@example.com",
#             delivery_method=AuthenticationProvider.EMAIL,
#             purpose=AuthenticationOtpPurpose.LOGIN, # Set purpose LOGIN
#             expired_at=future_time,
#             merchant_id=uuid.uuid4()
#         )
#         print(f"Object Created. Purpose: {otp.purpose}")

#         # Test Dynamic Attribute (Correct Purpose)
#         print(f"Check is_login (Expected True): {otp.is_login}")
#         assert otp.is_login is True

#         # Test Dynamic Attribute (Incorrect Purpose)
#         print(f"Check is_registration (Expected False): {otp.is_registration}")
#         assert otp.is_registration is False

#         # Test Boolean Magic Method (Valid Object)
#         print(f"Check Boolean validity (Expected True): {bool(otp)}")
#         assert bool(otp) is True
        
#         print(">> TEST 1 PASSED")
#     except Exception as e:
#         print(f">> TEST 1 FAILED: {e}")
#         traceback.print_exc()

#     # ---------------------------------------------------------
#     # TEST 2: ERROR HANDLING (Invalid Attributes)
#     # ---------------------------------------------------------
#     print("\n[TEST 2] AttributeError Handling")
#     try:
#         # Akses attribute ngawur yang tidak ada di pattern is_ atau field class
#         print("Accessing 'otp.random_attribute'...")
#         _ = otp.random_attribute
#         print(">> TEST 2 FAILED (Should raise AttributeError)")
#     except AttributeError as e:
#         print(f"Caught Expected Error: {e}")
#         print(">> TEST 2 PASSED")
#     except Exception as e:
#         print(f">> TEST 2 FAILED (Wrong Error Type): {e}")

#     # ---------------------------------------------------------
#     # TEST 3: STATE CHANGE (Mark Used)
#     # ---------------------------------------------------------
#     print("\n[TEST 3] Mark Used Logic")
#     try:
#         # Sebelum dipakai harusnya True
#         assert bool(otp) is True
        
#         otp.mark_used(now)
        
#         print(f"OTP Used Status: {otp.used}")
#         print(f"Check Boolean validity (Expected False): {bool(otp)}")
        
#         assert otp.used is True
#         assert otp.used_at == now
#         assert bool(otp) is False # Harus False karena sudah used
#         print(">> TEST 3 PASSED")
#     except Exception as e:
#         print(f">> TEST 3 FAILED: {e}")
#         traceback.print_exc()

#     # ---------------------------------------------------------
#     # TEST 4: EXPIRATION LOGIC
#     # ---------------------------------------------------------
#     print("\n[TEST 4] Expiration Logic")
#     try:
#         expired_otp = ManagementOtpDomain(
#             sid=uuid.uuid4(),
#             otp_code="000000",
#             otp_url="url",
#             delivery_target="target",
#             delivery_method=AuthenticationProvider.WHATSAPP,
#             purpose=AuthenticationOtpPurpose.REGISTRATION,
#             expired_at=past_time, # Set waktu lampau
#             merchant_id=uuid.uuid4()
#         )
        
#         print(f"Is Expired (Expected True): {expired_otp.is_expired()}")
#         print(f"Check Boolean validity (Expected False): {bool(expired_otp)}")
        
#         assert expired_otp.is_expired() is True
#         assert bool(expired_otp) is False
#         print(">> TEST 4 PASSED")
#     except Exception as e:
#         print(f">> TEST 4 FAILED: {e}")

#     # ---------------------------------------------------------
#     # TEST 5: URL GENERATION
#     # ---------------------------------------------------------
#     print("\n[TEST 5] URL Generation Logic")
#     try:
#         # Case A: URL bersih (belum ada query param)
#         url_clean = f"http://localhost/verify?code={otp.otp_code}"
#         result_clean = otp.gen_otp_url(otp.otp_code)
#         print(f"Input: {url_clean} -> Output: {result_clean}")
#         # Case B: URL kotor (sudah ada query param)
#         url_dirty = "http://localhost/verify?lang=id"
#         result_dirty = otp.gen_otp_url(url_dirty)
#         print(f"Input: {url_dirty} -> Output: {result_dirty}")
        
#         print(">> TEST 5 PASSED")
#     except Exception as e:
#         print(f">> TEST 5 FAILED: {e}")
#         traceback.print_exc()

#     # ---------------------------------------------------------
#     # TEST 6: TARGET MATCHING
#     # ---------------------------------------------------------
#     print("\n[TEST 6] Target Matching Logic")
#     try:
#         target_email = "user@example.com"
#         # Gunakan objek otp dari Test 1 yang targetnya user@example.com
        
#         print(f"Matching '{target_email}' (Expected True): {otp.match_target(target_email)}")
#         assert otp.match_target(target_email) is True

#         print(f"Matching 'wrong@mail.com' (Expected False): {otp.match_target('wrong@mail.com')}")
#         assert otp.match_target('wrong@mail.com') is False
        
#         print(">> TEST 6 PASSED")
#     except Exception as e:
#         print(f">> TEST 6 FAILED: {e}")

#     # print("\n=== END TESTING ===")
