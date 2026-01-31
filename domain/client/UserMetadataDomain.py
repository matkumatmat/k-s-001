from __future__  import annotations
from dataclasses import dataclass
from domain.management.ValueObject import ManagementDevices



@dataclass
class UserMetadataDomain:
    user_agent : str
    devices_width : int
    devices_length : int
    ip_address : str
    region: str
    lang: str

    @property
    def device_type(self) -> str:
        if self.devices_width < 768:
            return ManagementDevices.MOBILE
        elif 768 <= self.devices_width < 1024:
            return ManagementDevices.TABLET
        else:
            return ManagementDevices.DESKTOP

    def is_mobile(self) -> bool:
        return self.device_type == ManagementDevices.MOBILE

    def is_tablet(self) -> bool:
        return self.device_type == ManagementDevices.TABLET

    def is_desktop(self) -> bool:
        return self.device_type == ManagementDevices.DESKTOP


# if __name__ == "__main__":
#     import traceback
#     from domain.management.ValueObject import ManagementDevices

#     print("=== START TESTING ===")

#     print("\n[TEST 1] Mobile Device Detection (width < 768)")
#     try:
#         mobile_metadata = UserMetadataDomain(
#             user_agent="Mozilla/5.0 (iPhone)",
#             devices_width=375,
#             devices_length=667,
#             ip_address="192.168.1.1",
#             region="ID",
#             lang="id-ID"
#         )
#         print(f"Device type (Expected MOBILE): {mobile_metadata.device_type}")
#         print(f"is_mobile (Expected True): {mobile_metadata.is_mobile()}")
#         print(f"is_tablet (Expected False): {mobile_metadata.is_tablet()}")
#         print(f"is_desktop (Expected False): {mobile_metadata.is_desktop()}")

#         assert mobile_metadata.device_type == ManagementDevices.MOBILE
#         assert mobile_metadata.is_mobile() is True
#         assert mobile_metadata.is_tablet() is False
#         assert mobile_metadata.is_desktop() is False
#         print(">> TEST 1 PASSED")
#     except Exception as e:
#         print(f">> TEST 1 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 2] Tablet Device Detection (768 <= width < 1024)")
#     try:
#         tablet_metadata = UserMetadataDomain(
#             user_agent="Mozilla/5.0 (iPad)",
#             devices_width=768,
#             devices_length=1024,
#             ip_address="10.0.0.1",
#             region="US",
#             lang="en-US"
#         )
#         print(f"Device type (Expected TABLET): {tablet_metadata.device_type}")
#         print(f"is_tablet (Expected True): {tablet_metadata.is_tablet()}")
#         print(f"is_mobile (Expected False): {tablet_metadata.is_mobile()}")
#         print(f"is_desktop (Expected False): {tablet_metadata.is_desktop()}")

#         assert tablet_metadata.device_type == ManagementDevices.TABLET
#         assert tablet_metadata.is_tablet() is True
#         assert tablet_metadata.is_mobile() is False
#         assert tablet_metadata.is_desktop() is False
#         print(">> TEST 2 PASSED")
#     except Exception as e:
#         print(f">> TEST 2 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 3] Tablet Edge Case (width = 1023)")
#     try:
#         tablet_edge = UserMetadataDomain(
#             user_agent="Mozilla/5.0 (iPad Pro)",
#             devices_width=1023,
#             devices_length=1366,
#             ip_address="172.16.0.1",
#             region="SG",
#             lang="en-SG"
#         )
#         print(f"Device type (Expected TABLET): {tablet_edge.device_type}")
#         assert tablet_edge.device_type == ManagementDevices.TABLET
#         assert tablet_edge.is_tablet() is True
#         print(">> TEST 3 PASSED")
#     except Exception as e:
#         print(f">> TEST 3 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 4] Desktop Device Detection (width >= 1024)")
#     try:
#         desktop_metadata = UserMetadataDomain(
#             user_agent="Mozilla/5.0 (Windows NT 10.0)",
#             devices_width=1920,
#             devices_length=1080,
#             ip_address="203.0.113.1",
#             region="JP",
#             lang="ja-JP"
#         )
#         print(f"Device type (Expected DESKTOP): {desktop_metadata.device_type}")
#         print(f"is_desktop (Expected True): {desktop_metadata.is_desktop()}")
#         print(f"is_mobile (Expected False): {desktop_metadata.is_mobile()}")
#         print(f"is_tablet (Expected False): {desktop_metadata.is_tablet()}")

#         assert desktop_metadata.device_type == ManagementDevices.DESKTOP
#         assert desktop_metadata.is_desktop() is True
#         assert desktop_metadata.is_mobile() is False
#         assert desktop_metadata.is_tablet() is False
#         print(">> TEST 4 PASSED")
#     except Exception as e:
#         print(f">> TEST 4 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 5] Desktop Edge Case (width = 1024)")
#     try:
#         desktop_edge = UserMetadataDomain(
#             user_agent="Mozilla/5.0 (Macintosh)",
#             devices_width=1024,
#             devices_length=768,
#             ip_address="198.51.100.1",
#             region="AU",
#             lang="en-AU"
#         )
#         print(f"Device type (Expected DESKTOP): {desktop_edge.device_type}")
#         assert desktop_edge.device_type == ManagementDevices.DESKTOP
#         assert desktop_edge.is_desktop() is True
#         print(">> TEST 5 PASSED")
#     except Exception as e:
#         print(f">> TEST 5 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 6] Extreme Small Width (width = 320)")
#     try:
#         small_mobile = UserMetadataDomain(
#             user_agent="Mozilla/5.0 (iPhone SE)",
#             devices_width=320,
#             devices_length=568,
#             ip_address="192.0.2.1",
#             region="IN",
#             lang="hi-IN"
#         )
#         print(f"Device type (Expected MOBILE): {small_mobile.device_type}")
#         assert small_mobile.device_type == ManagementDevices.MOBILE
#         print(">> TEST 6 PASSED")
#     except Exception as e:
#         print(f">> TEST 6 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 7] Extreme Large Width (width = 3840)")
#     try:
#         large_desktop = UserMetadataDomain(
#             user_agent="Mozilla/5.0 (X11; Linux x86_64)",
#             devices_width=3840,
#             devices_length=2160,
#             ip_address="203.0.113.42",
#             region="KR",
#             lang="ko-KR"
#         )
#         print(f"Device type (Expected DESKTOP): {large_desktop.device_type}")
#         assert large_desktop.device_type == ManagementDevices.DESKTOP
#         print(">> TEST 7 PASSED")
#     except Exception as e:
#         print(f">> TEST 7 FAILED: {e}")
#         traceback.print_exc()

#     print("\n[TEST 8] Boundary Test (width = 767 - Just Below Tablet)")
#     try:
#         boundary_mobile = UserMetadataDomain(
#             user_agent="Mozilla/5.0",
#             devices_width=767,
#             devices_length=1024,
#             ip_address="10.10.10.10",
#             region="CN",
#             lang="zh-CN"
#         )
#         print(f"Device type (Expected MOBILE): {boundary_mobile.device_type}")
#         assert boundary_mobile.device_type == ManagementDevices.MOBILE
#         print(">> TEST 8 PASSED")
#     except Exception as e:
#         print(f">> TEST 8 FAILED: {e}")
#         traceback.print_exc()

#     print("\n=== END TESTING ===")
