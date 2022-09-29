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


class Context:
    async def send(self, destination: str, message: BaseModel):
        print('I should send', destination, message.dict())


async def _run_interval(func: Callable[[], Awaitable[None]], ctx: Context, period: float):
    while True:
        await asyncio.sleep(period)
        await func(ctx)


class Agent:
    def __init__(self):
        self._intervals: List[Tuple[float, Any]] = []
        self._background_tasks = set()
        self._loop = asyncio.get_event_loop()
        self._ctx = Context()

    @property
    def address(self) -> str:
        return 'not-implemented'

    def update_loop(self, loop):
        self._loop = loop

    def on_interval(self, period: float):
        def decorator_on_interval(func):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            # register the interval with the agent
            task = self._loop.create_task(_run_interval(func, self._ctx, period))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            return handler

        return decorator_on_interval

    def on_message(self, model):
        def decorator_on_message(func):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            return handler

        return decorator_on_message

    def run(self):
        self._loop.run_forever()


class Bureau:
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._agents = []

    def add(self, agent: Agent):
        agent.update_loop(self._loop)
        self._agents.append(agent)

    def run(self):
        self._loop.run_forever()
