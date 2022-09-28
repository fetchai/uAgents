import asyncio
import functools
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel


class Envelope(BaseModel):
    version: int
    headers: Dict[str, str]
    payload: bytes
    signature: Optional[str]


async def _run_interval(func: Callable[[], Awaitable[None]], period: float):
    while True:
        await asyncio.sleep(period)
        await func()


class Agent:
    def __init__(self):
        self._intervals: List[Tuple[float, Any]] = []
        self._background_tasks = set()
        self._loop = asyncio.get_event_loop()

    def on_interval(self, period: float):
        def decorator_on_interval(func):
            @functools.wraps(func)
            def handler(*args, **kargs):
                return func(*args, **kargs)

            # register the interval with the agent
            task = self._loop.create_task(_run_interval(func, period))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            return handler

        return decorator_on_interval

    def run(self):
        self._loop.run_forever()