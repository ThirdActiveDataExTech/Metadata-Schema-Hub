import os
from datetime import datetime

VERSION = os.getenv("APP_VERSION", "Unknown")
BUILD_DATE = os.getenv("BUILD_DATE", "Unknown")

STARTED_AT = datetime.now()


def get_uptime() -> str:
    delta = datetime.now() - STARTED_AT
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h{minutes}m{seconds}s"
