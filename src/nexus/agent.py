import asyncio
import functools
import json
from typing import Optional, List, Tuple, Any

import pydantic
import uvicorn

from nexus.context import Context, IntervalCallback, MessageCallback
from nexus.crypto import Identity
from nexus.dispatch import Sink, dispatcher
from nexus.envelope import Envelope
from nexus.models import Model
from nexus.protocol import Protocol
from nexus.resolver import Resolver, AlmanacResolver
from nexus.storage import KeyValueStore


async def _run_interval(func: IntervalCallback, ctx: Context, period: float):
    while True:
        await func(ctx)
        await asyncio.sleep(period)


async def _read_asgi_body(receive):
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)

    return body


class Agent(Sink):
    def __init__(
        self,
        name: Optional[str] = None,
        port: Optional[int] = None,
        seed: Optional[str] = None,
        resolve: Optional[Resolver] = None,
    ):
        self._name = name
        self._intervals: List[Tuple[float, Any]] = []
        self._port = port if port is not None else 8000
        self._background_tasks = set()
        self._resolver = resolve if resolve is not None else AlmanacResolver()
        self._loop = asyncio.get_event_loop_policy().get_event_loop()
        self._identity = (
            Identity.generate() if seed is None else Identity.from_seed(seed)
        )
        self._storage = KeyValueStore(self.address[0:16])
        self._ctx = Context(
            self._identity.address,
            self._name,
            self._storage,
            self._resolver,
            self._identity,
        )
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

            schema_digest = Model.build_schema_digest(model)

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

    async def handle_message(self, sender, schema_digest: str, message: Any):
        # schema_digest = _build_model_digest(message)
        await self._message_queue.put((schema_digest, sender, message))

    async def run_inner(self):
        config = uvicorn.Config(self, host="0.0.0.0", port=self._port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    def run(self, port: Optional[int] = None):
        self._loop.run_until_complete(self.run_inner())

    # ASGI interface
    async def __call__(self, scope, receive, send):
        assert scope["type"] == "http"

        if scope["path"] != "/submit":
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {"type": "http.response.body", "body": b'{"error": "not found"}'}
            )

        headers = {k: v for k, v in scope.get("headers", {})}
        if headers[b"content-type"] != b"application/json":
            await send(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {"type": "http.response.body", "body": b'{"error": "invalid format"}'}
            )

        # read the entire payload
        raw_contents = await _read_asgi_body(receive)
        contents = json.loads(raw_contents.decode())

        try:
            env = Envelope.parse_obj(contents)
        except pydantic.ValidationError:
            await send(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {"type": "http.response.body", "body": b'{"error": "invalid format"}'}
            )
            return

        if not env.verify():
            await send(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "unable to verify payload"}',
                }
            )
            return

        if not dispatcher.contains(env.target):
            await send(
                {
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [
                        [b"content-type", b"application/json"],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"error": "unable to route envelope"}',
                }
            )
            return

        await dispatcher.dispatch(
            env.sender, env.target, env.protocol, env.decode_payload()
        )

        body = f'Received {scope["method"]} request to {scope["path"]}'
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"application/json"],
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"{}",
            }
        )

    async def _process_message_queue(self):
        while True:
            # get an element from the queue
            schema_digest, sender, message = await self._message_queue.get()

            # lookup the model definition
            ModelKlass = self._models.get(schema_digest)
            if ModelKlass is None:
                continue

            # parse the received message
            recovered = ModelKlass.parse_raw(message)

            # attempt to find the handler
            handler: MessageCallback = self._message_handlers.get(schema_digest)
            if handler is not None:
                await handler(self._ctx, sender, recovered)


class Bureau:
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._agents = []

    def add(self, agent: Agent):
        agent.update_loop(self._loop)
        self._agents.append(agent)

    def run(self):
        self._loop.run_forever()
