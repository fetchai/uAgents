import asyncio
import functools
import logging
from typing import Optional, List, Set, Tuple, Any, Union

from apispec import APISpec

from cosmpy.aerial.wallet import LocalWallet, PrivateKey

from nexus.asgi import ASGIServer
from nexus.context import Context, IntervalCallback, MessageCallback, MsgDigest
from nexus.crypto import Identity, derive_key_from_seed
from nexus.dispatch import Sink, dispatcher
from nexus.models import Model
from nexus.protocol import Protocol, OPENAPI_VERSION
from nexus.resolver import Resolver, AlmanacResolver
from nexus.storage import KeyValueStore, get_wallet_key
from nexus.network import get_ledger, get_reg_contract
from nexus.config import (
    REG_UPDATE_INTERVAL_SECONDS,
    REGISTRATION_FEE,
    REGISTRATION_DENOM,
    LEDGER_PREFIX,
)


async def _run_interval(func: IntervalCallback, ctx: Context, period: float):
    while True:
        try:
            await func(ctx)
        except OSError:
            logging.exception("OS Error in interval handler")
        except RuntimeError:
            logging.exception("Runtime Error in interval handler")

        await asyncio.sleep(period)


class Agent(Sink):
    def __init__(
        self,
        name: Optional[str] = None,
        port: Optional[int] = None,
        seed: Optional[str] = None,
        endpoint: Optional[str] = None,
        resolve: Optional[Resolver] = None,
        version: Optional[str] = None,
    ):
        self._name = name
        self._intervals: List[Tuple[float, Any]] = []
        self._port = port if port is not None else 8000
        self._background_tasks = set()
        self._resolver = resolve if resolve is not None else AlmanacResolver()
        self._loop = asyncio.get_event_loop_policy().get_event_loop()
        if seed is None:
            if name is None:
                self._wallet = LocalWallet.generate()
                self._identity = Identity.generate()
            else:
                self._wallet = LocalWallet(get_wallet_key(name))
                self._identity = Identity.get_identity(name)
        else:
            self._identity = Identity.from_seed(seed, 0)
            self._wallet = LocalWallet(
                PrivateKey(derive_key_from_seed(seed, LEDGER_PREFIX, 0)),
                prefix=LEDGER_PREFIX,
            )
        self._endpoint = endpoint if endpoint is not None else ""
        self._ledger = get_ledger()
        self._reg_contract = get_reg_contract()
        self._storage = KeyValueStore(self.address[0:16])
        self._models = {}
        self._replies = {}
        self._message_handlers = {}
        self._inbox = {}
        self._ctx = Context(
            self._identity.address,
            self._name,
            self._storage,
            self._resolver,
            self._identity,
            self._wallet,
            self._ledger,
        )
        self._dispatcher = dispatcher
        self._message_queue = asyncio.Queue()
        self._version = version or "0.1.0"

        self.spec = APISpec(
            title=name,
            version=self._version,
            openapi_version=OPENAPI_VERSION,
        )

        # register with the dispatcher
        self._dispatcher.register(self.address, self)

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

    def sign_registration(self) -> str:
        return self._identity.sign_registration(
            self._reg_contract.address, self.get_registration_sequence()
        )

    def update_loop(self, loop):
        self._loop = loop

    async def register(self, ctx: Context):

        if self.registration_status():
            logging.info(
                f"Agent {self._name} registration is up to date\
                    \nWallet address: {self.wallet.address()}"
            )
            return

        agent_balance = ctx.ledger.query_bank_balance(ctx.wallet)

        if agent_balance < REGISTRATION_FEE:
            raise Exception(
                f"Insufficient funds to register {self._name}\
                    \nFund using wallet address: {self.wallet.address()}"
            )

        signature = self.sign_registration()

        msg = {
            "register": {
                "record": {
                    "service": {
                        "protocols": list(self._models.keys()),
                        "endpoints": [{"url": self._endpoint, "weight": 1}],
                    }
                },
                "signature": signature,
                "sequence": self.get_registration_sequence(),
                "agent_address": self.address,
            }
        }

        logging.info(f"Registering Agent {self._name}...")
        transaction = await self._loop.run_in_executor(
            None,
            functools.partial(
                self._reg_contract.execute,
                msg,
                ctx.wallet,
                funds=f"{REGISTRATION_FEE}{REGISTRATION_DENOM}",
            ),
        )
        await self._loop.run_in_executor(None, transaction.wait_to_complete)
        logging.info(
            f"Registering Agent {self._name}...complete\nWallet address: {self.wallet.address()}"
        )

    def registration_status(self) -> bool:

        query_msg = {"query_records": {"agent_address": self.address}}

        if self._reg_contract.query(query_msg)["record"] != []:
            return True

        return False

    def get_registration_sequence(self) -> int:
        query_msg = {"query_sequence": {"agent_address": self.address}}
        sequence = query_msg.get("sequence", 0)

        return sequence

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

    def on_message(
        self, model: Model, replies: Optional[Union[Model, Set[Model]]] = None
    ):
        def decorator_on_message(func: MessageCallback):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._add_message_handler(model, func, replies)

            return handler

        return decorator_on_message

    def _add_message_handler(self, model, func, replies):
        schema_digest = Model.build_schema_digest(model)

        # update the model database
        self._models[schema_digest] = model
        self._message_handlers[schema_digest] = func
        if replies is not None:
            if not isinstance(replies, set):
                replies = {replies}
            self._replies[schema_digest] = {
                Model.build_schema_digest(reply) for reply in replies
            }

            self.spec.path(
                path=model.__name__,
                operations=dict(
                    post=dict(replies=[reply.__name__ for reply in replies])
                ),
            )

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
            self._replies[schema_digest] = protocol.replies[schema_digest]
            self._message_handlers[schema_digest] = protocol.message_handlers[
                schema_digest
            ]

    async def handle_message(self, sender, schema_digest: str, message: Any):
        # schema_digest = _build_model_digest(message)
        await self._message_queue.put((schema_digest, sender, message))

    def run(self):
        # start the contract registration update loop
        self._loop.create_task(
            _run_interval(self.register, self._ctx, REG_UPDATE_INTERVAL_SECONDS)
        )

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

            context = Context(
                self._identity.address,
                self._name,
                self._storage,
                self._resolver,
                self._identity,
                self._wallet,
                self._ledger,
                self._replies,
                MsgDigest(message=message, schema_digest=schema_digest),
            )

            # attempt to find the handler
            handler: MessageCallback = self._message_handlers.get(schema_digest)
            if handler is not None:
                await handler(context, sender, recovered)


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
