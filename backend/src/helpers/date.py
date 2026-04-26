import datetime
from zoneinfo import ZoneInfo

from src.config import settings


def datetime_formatter(value: datetime.datetime):
    if not value:
        return ''

    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)

    local_timezone = ZoneInfo(settings.TZ)
    local_time = value.astimezone(local_timezone)

    return local_time.strftime("%Y-%m-%d %H:%M")
