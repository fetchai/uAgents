import asyncio
import functools
import logging
from typing import Optional, List, Tuple, Any

from cosmpy.aerial.wallet import LocalWallet

from nexus.asgi import ASGIServer
from nexus.context import Context, IntervalCallback, MessageCallback
from nexus.crypto import Identity
from nexus.dispatch import Sink, dispatcher
from nexus.models import Model
from nexus.protocol import Protocol
from nexus.resolver import Resolver, AlmanacResolver
from nexus.storage import KeyValueStore
from nexus.network import get_ledger, get_reg_contract, get_wallet


async def _run_interval(func: IntervalCallback, ctx: Context, period: float):
    while True:
        try:
            if ctx is None:
                await func()
            else:
                await func(ctx)
        except OSError:
            logging.exception("OS Error in interval handler")
        except RuntimeError:
            logging.exception("Runtime Error in interval handler")

        await asyncio.sleep(period)


REGISTRATION_FEE = "500000000000000000atestfet"
REG_UPDATE_INTERVAL_SECONDS = 60


class Agent(Sink):
    def __init__(
        self,
        name: Optional[str] = None,
        port: Optional[int] = None,
        seed: Optional[str] = None,
        endpoint: Optional[str] = None,
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
        self._endpoint = endpoint if endpoint is not None else "123"
        self._wallet = get_wallet(Identity.get_key(self.address))
        self._ledger = get_ledger("fetchai-testnet")
        self._reg_contract = get_reg_contract(self._ledger)
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

        # start the contract registration update loop
        self._loop.create_task(
            _run_interval(self.register, None, REG_UPDATE_INTERVAL_SECONDS)
        )

        # start the background message queue processor
        task = self._loop.create_task(self._process_message_queue())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        self._server = ASGIServer(self._port, self._loop)

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name
        return self.address[:10]

    @property
    def address(self) -> str:
        return self._identity.address

    @property
    def wallet(self) -> LocalWallet:
        return self._wallet

    def sign_digest(self, digest: bytes) -> str:
        return self._identity.sign_digest(digest)

    def update_loop(self, loop):
        self._loop = loop

    async def register(self):

        if self.registration_status():
            print(f"Agent {self._name} registration is up to date")
            return

        msg = {
            "register": {
                "record": {
                    "Service": {
                        "protocols": list(self._models.keys()),
                        "endpoints": [{"url": self._endpoint, "weight": 1}],
                    }
                }
            }
        }

        await self._reg_contract.execute(
            msg, self._wallet, funds=REGISTRATION_FEE
        ).wait_to_complete()
        print(f"Registration complete for Agent {self._name}")

    def registration_status(self) -> bool:

        ledger = get_ledger("fetchai-testnet")
        contract = get_reg_contract(ledger)

        query_msg = {"query_records": {"address": self._wallet.address()}}

        if contract.query(query_msg)["record"] != []:
            return True

        return False

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

    def run(self):
        self._loop.run_until_complete(self._server.serve())

    async def _process_message_queue(self):
        while True:
            # get an element from the queue
            schema_digest, sender, message = await self._message_queue.get()

            # lookup the model definition
            model_class = self._models.get(schema_digest)
            if model_class is None:
                continue

            # parse the received message
            recovered = model_class.parse_raw(message)

            # attempt to find the handler
            handler: MessageCallback = self._message_handlers.get(schema_digest)
            if handler is not None:
                await handler(self._ctx, sender, recovered)


class Bureau:
    def __init__(self, port: Optional[int] = None):
        self._loop = asyncio.get_event_loop_policy().get_event_loop()
        self._agents = []
        self._port = port or 8000
        self._server = ASGIServer(self._port, self._loop)

    def add(self, agent: Agent):
        agent.update_loop(self._loop)
        self._agents.append(agent)

    def run(self):
        self._loop.run_until_complete(self._server.serve())
