import functools
import time
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel


class Envelope(BaseModel):
    version: int
    headers: Dict[str, str]
    payload: bytes
    signature: Optional[str]


class Agent:
    def __init__(self):
        self._intervals: List[Tuple[float, Any]] = []

    def on_interval(self, period: float):
        def decorator_on_interval(func):
            @functools.wraps(func)
            def handler(*args, **kargs):
                print("Calling wrapped")
                return func(*args, **kargs)

            print("Registering the interval with the agent")
            # keep a copy
            self._intervals.append((period, handler))
            return handler

        return decorator_on_interval

    def run(self):
        while True:
            print("Running here honestly...")
            time.sleep(1)
