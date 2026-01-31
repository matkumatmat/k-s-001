from enum import Enum

class LogType(str, Enum):
    SYSTEM = "SYSTEM"
    USER_BEHAVIOR = "USER_BEHAVIOR"
    SESSION = "SESSION"
