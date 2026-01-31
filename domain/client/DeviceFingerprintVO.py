from __future__ import annotations
from dataclasses import dataclass
import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.client.UserMetadataDomain import UserMetadataDomain


@dataclass(frozen=True)
class DeviceFingerprintVO:
    _raw_fingerprint: str

    @classmethod
    def from_metadata(cls, metadata: UserMetadataDomain) -> DeviceFingerprintVO:
        raw = f"{metadata.devices_width}-{metadata.devices_length}-{metadata.user_agent}-{metadata.ip_address}-{metadata.region}-{metadata.lang}"
        return cls(_raw_fingerprint=raw)

    @classmethod
    def from_encoded(cls, encoded: str) -> DeviceFingerprintVO:

        decoded_bytes = base64.b64decode(encoded.encode('utf-8'))
        raw = decoded_bytes.decode('utf-8')
        return cls(_raw_fingerprint=raw)

    @property
    def raw(self) -> str:
        return self._raw_fingerprint

    @property
    def encoded(self) -> str:
        encoded_bytes = base64.b64encode(self._raw_fingerprint.encode('utf-8'))
        return encoded_bytes.decode('utf-8')

    def matches(self, other: DeviceFingerprintVO) -> bool:
        if not isinstance(other, DeviceFingerprintVO):
            return False
        return self.encoded == other.encoded

    def __str__(self) -> str:
        return self.encoded

    def __repr__(self) -> str:
        return f"DeviceFingerprintVO(raw='{self.raw[:50]}...')"


# if __name__ == "__main__":
#     import traceback
#     from domain.client.UserMetadataDomain import UserMetadataDomain

#     print("=== START TESTING ===")

#     metadata_1 = UserMetadataDomain(
#         user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
#         devices_width=375,
#         devices_length=667,
#         ip_address="192.168.1.100",
#         region="ID",
#         lang="id-ID"
#     )

#     metadata_2 = UserMetadataDomain(
#         user_agent="Mozilla/5.0 (Windows NT 10.0)",
#         devices_width=1920,
#         devices_length=1080,
#         ip_address="10.0.0.1",
#         region="US",
#         lang="en-US"
#     )

#     print("\n[TEST 1] Fingerprint Creation from Metadata")
#     try:
#         fp1 = DeviceFingerprintVO.from_metadata(metadata_1)
#         print(f"Raw fingerprint: {fp1.raw}")
#         print(f"Encoded fingerprint: {fp1.encoded}")
#         assert fp1.raw == "375-667-Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)-192.168.1.100-ID-id-ID"
#         assert len(fp1.encoded) > 0
#         print(">> TEST 1 PASSED")
#     except Exception as e:
#         print(f">> TEST 1 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 2] Encoded/Decoded Round-Trip")
#     try:
#         fp_original = DeviceFingerprintVO.from_metadata(metadata_1)
#         encoded_str = fp_original.encoded
#         fp_reconstructed = DeviceFingerprintVO.from_encoded(encoded_str)

#         print(f"Original raw: {fp_original.raw}")
#         print(f"Reconstructed raw: {fp_reconstructed.raw}")

#         assert fp_original.raw == fp_reconstructed.raw
#         assert fp_original.encoded == fp_reconstructed.encoded
#         print(">> TEST 2 PASSED")
#     except Exception as e:
#         print(f">> TEST 2 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 3] Fingerprint Matching (Same Metadata)")
#     try:
#         fp1_a = DeviceFingerprintVO.from_metadata(metadata_1)
#         fp1_b = DeviceFingerprintVO.from_metadata(metadata_1)

#         print(f"FP1_A matches FP1_B (Expected True): {fp1_a.matches(fp1_b)}")
#         assert fp1_a.matches(fp1_b) is True
#         print(">> TEST 3 PASSED")
#     except Exception as e:
#         print(f">> TEST 3 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 4] Fingerprint Not Matching (Different Metadata)")
#     try:
#         fp1 = DeviceFingerprintVO.from_metadata(metadata_1)
#         fp2 = DeviceFingerprintVO.from_metadata(metadata_2)

#         print(f"FP1 matches FP2 (Expected False): {fp1.matches(fp2)}")
#         assert fp1.matches(fp2) is False
#         print(">> TEST 4 PASSED")
#     except Exception as e:
#         print(f">> TEST 4 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 5] Immutability Check")
#     try:
#         fp = DeviceFingerprintVO.from_metadata(metadata_1)
#         print("Attempting to modify _raw_fingerprint...")
#         fp._raw_fingerprint = "modified"
#         print(">> TEST 5 FAILED (Should raise FrozenInstanceError)")
#     except Exception as e:
#         print(f"Caught expected error: {type(e).__name__}")
#         print(">> TEST 5 PASSED")

#     print("\n[TEST 6] Invalid Type Matching")
#     try:
#         fp = DeviceFingerprintVO.from_metadata(metadata_1)
#         result = fp.matches("not_a_fingerprint")
#         print(f"FP matches string (Expected False): {result}")
#         assert result is False
#         print(">> TEST 6 PASSED")
#     except Exception as e:
#         print(f">> TEST 6 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 7] String Representation")
#     try:
#         fp = DeviceFingerprintVO.from_metadata(metadata_1)
#         str_repr = str(fp)
#         print(f"String representation: {str_repr}")
#         assert str_repr == fp.encoded
#         print(">> TEST 7 PASSED")
#     except Exception as e:
#         print(f">> TEST 7 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 8] Invalid Base64 Decoding")
#     try:
#         print("Attempting to decode invalid base64...")
#         DeviceFingerprintVO.from_encoded("invalid@@@base64!!!")
#         print(">> TEST 8 FAILED (Should raise decoding error)")
#     except Exception as e:
#         print(f"Caught expected error: {type(e).__name__}")
#         print(">> TEST 8 PASSED")

#     print("\n=== END TESTING ===")
