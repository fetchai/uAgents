"""Cron-style schedules"""

import time
from collections.abc import Iterator
from datetime import datetime, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from cronsim import CronSim, CronSimError


class Cron:
    """
    A cron schedule evaluated in the given timezone (UTC by default).
    """

    def __init__(self, expression: str, tz: str | tzinfo | None = None):
        self.expression = expression
        try:
            self.tz = ZoneInfo(tz) if isinstance(tz, str) else tz or timezone.utc
        except (ZoneInfoNotFoundError, ValueError) as ex:
            raise ValueError(f"Invalid timezone '{tz}': {ex}") from ex
        try:
            CronSim(expression, datetime.now(self.tz))
        except CronSimError as ex:
            raise ValueError(f"Invalid cron expression '{expression}': {ex}") from ex

    def __repr__(self) -> str:
        return f"Cron({self.expression!r}, tz={self.tz!r})"

    def delays(self) -> Iterator[float]:
        """
        Yield the number of seconds to wait until each successive scheduled time,
        skipping any times that have already passed.
        """
        for t in CronSim(self.expression, datetime.now(self.tz)):
            # compare timestamps, as same-tz datetime arithmetic ignores DST shifts
            delay = t.timestamp() - time.time()
            if delay > 0:
                yield delay
