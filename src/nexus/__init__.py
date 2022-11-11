import asyncio
import functools
import hashlib
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel

from nexus.crypto import Identity
from nexus.dispatch import Dispatcher, Sink


class Envelope(BaseModel):
    version: int
    headers: Dict[str, str]
    payload: bytes
    signature: Optional[str]


dispatcher = Dispatcher()


class Model(BaseModel):
    pass


class KeyValueStore:
    def __init__(self):
        self._data = {}

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    def has(self, key: str) -> bool:
        return key in self._data

    def set(self, key: str, value: Any):
        self._data[key] = value

    def remove(self, key: str):
        if key in self._data:
            del self._data[key]

    def clear(self):
        self._data.clear()


class Context:
    def __init__(self, address: str, name: Optional[str], storage: KeyValueStore):
        self.storage = storage
        self._name = name
        self._address = str(address)

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        return self._address[:10]

    @property
    def address(self) -> str:
        return self._address

    async def send(self, destination: str, message: Model):
        await dispatcher.dispatch(self.address, destination, message)


IntervalCallback = Callable[[Context], Awaitable[None]]
MessageCallback = Callable[[Context, str, Any], Awaitable[None]]


async def _run_interval(func: IntervalCallback, ctx: Context, period: float):
    while True:
        await func(ctx)
        await asyncio.sleep(period)


def _build_model_digest(model):
    return (
        hashlib.sha256(model.schema_json(indent=None, sort_keys=True).encode("utf8"))
        .digest()
        .hex()
    )


class Protocol:
    def __init__(self):
        self._intervals = []
        self._message_handlers = {}
        self._models = {}

    @property
    def intervals(self):
        return self._intervals

    @property
    def models(self):
        return self._models

    @property
    def message_handlers(self):
        return self._message_handlers

    def on_interval(self, period: float):
        def decorator_on_interval(func: IntervalCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            # store the interval handler for later
            self._intervals.append((func, period))

            return handler

        return decorator_on_interval

    def on_message(self, model):
        def decorator_on_message(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            schema_digest = _build_model_digest(model)

            # update the model database
            self._models[schema_digest] = model
            self._message_handlers[schema_digest] = func

            return handler

        return decorator_on_message


class Agent(Sink):
    def __init__(self, name: Optional[str] = None, seed: Optional[str] = None):
        self._name = name
        self._intervals: List[Tuple[float, Any]] = []
        self._background_tasks = set()
        self._loop = asyncio.get_event_loop()
        self._identity = (
            Identity.generate() if seed is None else Identity.from_seed(seed)
        )
        self._storage = KeyValueStore()
        self._ctx = Context(self._identity.address, self._name, self._storage)
        self._models = {}
        self._message_handlers = {}
        self._dispatcher = dispatcher
        self._message_queue = asyncio.Queue()

        # register with the dispatcher
        self._dispatcher.register(self.address, self)

        # start the background message queue processor
        task = self._loop.create_task(self._process_message_queue())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        return self.address[:10]

    @property
    def address(self) -> str:
        return self._identity.address

    def sign_digest(self, digest: bytes) -> str:
        return self._identity.sign_digest(digest)

    def update_loop(self, loop):
        self._loop = loop

    def on_interval(self, period: float):
        def decorator_on_interval(func: IntervalCallback):
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
        def decorator_on_message(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            schema_digest = _build_model_digest(model)

            # update the model database
            self._models[schema_digest] = model
            self._message_handlers[schema_digest] = func

            return handler

        return decorator_on_message

    def include(self, protocol: Protocol):
        for func, period in protocol.intervals:
            task = self._loop.create_task(_run_interval(func, self._ctx, period))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        for schema_digest in protocol.models:
            if schema_digest in self._models:
                raise RuntimeError("Unable to register duplicate model")
            if schema_digest in self._message_handlers:
                raise RuntimeError("Unable to register duplicate message handler")
            if schema_digest not in protocol.message_handlers:
                raise RuntimeError("Unable to lookup up message handler in protocol")

            # include the message handlers from the protocol
            self._models[schema_digest] = protocol.models[schema_digest]
            self._message_handlers[schema_digest] = protocol.message_handlers[
                schema_digest
            ]

    async def handle_message(self, sender, message):
        schema_digest = _build_model_digest(message)
        await self._message_queue.put((schema_digest, sender, message))

    def run(self):
        self._loop.run_forever()

    async def _process_message_queue(self):
        while True:
            # get an element from the queue
            schema_digest, sender, message = await self._message_queue.get()

            # attempt to find the handler
            handler: MessageCallback = self._message_handlers.get(schema_digest)
            if handler is not None:
                await handler(self._ctx, sender, message)


class Bureau:
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._agents = []

    def add(self, agent: Agent):
        agent.update_loop(self._loop)
        self._agents.append(agent)

    def run(self):
        self._loop.run_forever()
