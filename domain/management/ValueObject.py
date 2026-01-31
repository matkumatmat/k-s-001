from enum import Enum
# User layer
class AuthenticationProvider(str, Enum):
    WHATSAPP = "whatsapp"
    PHONE = "phone"
    EMAIL =  "email"


# Management Layer
class AuthenticationRole(str, Enum):
    MANAGEMER = "d671c0c27eb2bf5ae041501cf7fd23d2"
    USER =  "5c9917a60ea23829bef2d1851181682a"

class AuthenticationOtpPurpose(str, Enum):
    REGISTRATION = "registration"
    LOGIN = "login"
    CHANGECONTACT ="change_contact"
    CHANGE_PASSWORD = "change_password"
    FORGOT_PASSWORD = "forgot_password"
    VERIFICATION = "verification"

class ManagementDevices(str, Enum):
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"

