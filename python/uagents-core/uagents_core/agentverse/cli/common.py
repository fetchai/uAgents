import logging
from datetime import datetime, timedelta, timezone

from uagents_core.config import AgentverseConfig

logging.getLogger("uagents_core.utils.resolver").setLevel(logging.ERROR)

DEFAULT_REQUESTS_TIMEOUT = 10


def compact_timedelta(td: timedelta) -> str:
    return str(td).split(".", maxsplit=1)[0]


def parse_agentverse_config(url: str) -> AgentverseConfig:
    prefix, base = url.split("://")
    return AgentverseConfig(base_url=base, http_prefix=prefix)


def _datetime_fmt(t: datetime) -> str:
    now = datetime.now(timezone.utc)
    t = t.replace(tzinfo=timezone.utc)

    if t.timestamp() < now.timestamp():
        period = f"{now - t} ago"
    elif now.timestamp() < t.timestamp():
        period = f"{t - now} to go"
    else:
        period = ""

    return f"{t.strftime('%A, %B %d, %H:%M:%S, %Y')} ({period})"
