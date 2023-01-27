import asyncio
import functools
import logging
from typing import Dict, List, Optional, Set, Union

from cosmpy.aerial.wallet import LocalWallet, PrivateKey

from uagents.asgi import ASGIServer
from uagents.context import (
    Context,
    EventCallback,
    IntervalCallback,
    MessageCallback,
    MsgDigest,
)
from uagents.crypto import Identity, derive_key_from_seed, is_user_address
from uagents.dispatch import Sink, dispatcher, JsonStr
from uagents.models import Model, ErrorMessage
from uagents.protocol import Protocol
from uagents.resolver import Resolver, AlmanacResolver
from uagents.storage import KeyValueStore, get_or_create_private_keys
from uagents.network import get_ledger, get_reg_contract
from uagents.config import (
    REGISTRATION_FEE,
    REGISTRATION_DENOM,
    LEDGER_PREFIX,
    BLOCK_INTERVAL,
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


async def _handle_error(ctx: Context, destination: str, msg: ErrorMessage):
    await ctx.send(destination, msg)


class Agent(Sink):
    def __init__(
        self,
        name: Optional[str] = None,
        port: Optional[int] = None,
        seed: Optional[str] = None,
        endpoint: Optional[Union[List[str], Dict[str, dict]]] = None,
        resolve: Optional[Resolver] = None,
        version: Optional[str] = None,
    ):
        self._name = name
        self._port = port if port is not None else 8000
        self._background_tasks: Set[asyncio.Task] = set()
        self._resolver = resolve if resolve is not None else AlmanacResolver()
        self._loop = asyncio.get_event_loop_policy().get_event_loop()
        if seed is None:
            if name is None:
                self._wallet = LocalWallet.generate()
                self._identity = Identity.generate()
            else:
                identity_key, wallet_key = get_or_create_private_keys(name)
                self._wallet = LocalWallet(PrivateKey(wallet_key))
                self._identity = Identity.from_string(identity_key)
        else:
            self._identity = Identity.from_seed(seed, 0)
            self._wallet = LocalWallet(
                PrivateKey(derive_key_from_seed(seed, LEDGER_PREFIX, 0)),
                prefix=LEDGER_PREFIX,
            )
        self._endpoint = endpoint
        self._ledger = get_ledger()
        self._reg_contract = get_reg_contract()
        self._storage = KeyValueStore(self.address[0:16])
        self._interval_messages: Set[str] = set()
        self._signed_message_handlers: Dict[str, MessageCallback] = {}
        self._unsigned_message_handlers: Dict[str, MessageCallback] = {}
        self._models: Dict[str, Model] = {}
        self._replies: Dict[str, Set[Model]] = {}
        self._queries: Dict[str, asyncio.Future] = {}
        self._ctx = Context(
            self._identity.address,
            self._name,
            self._storage,
            self._resolver,
            self._identity,
            self._wallet,
            self._ledger,
            self._queries,
            replies=self._replies,
            interval_messages=self._interval_messages,
        )
        self._dispatcher = dispatcher
        self._message_queue = asyncio.Queue()
        self._on_startup = []
        self._on_shutdown = []
        self._version = version or "0.1.0"

        # initialize the internal agent protocol
        self._protocol = Protocol(name=self._name, version=self._version)

        # keep track of supported protocols
        self.protocols = {}

        # register with the dispatcher
        self._dispatcher.register(self.address, self)

        self._server = ASGIServer(self._port, self._loop, self._queries)

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

    def update_queries(self, queries):
        self._queries = queries

    async def register(self, ctx: Context):

        agent_balance = ctx.ledger.query_bank_balance(ctx.wallet)

        if self._endpoint is None:
            logging.warning(
                "Agent has no endpoint and won't be able to receive external messages"
            )
            endpoints = []
        elif isinstance(self._endpoint, dict):
            endpoints = [
                {"url": val[0], "weight": val[1].get("weight") or 1}
                for val in self._endpoint.items()
            ]
        else:
            endpoints = [{"url": val, "weight": 1} for val in self._endpoint]

        if agent_balance < REGISTRATION_FEE:
            logging.warning(
                f"Agent does not have enough funds to register on Almanac contract\
                    \nFund using wallet address: {self.wallet.address()}"
            )
            return

        signature = self.sign_registration()

        msg = {
            "register": {
                "record": {
                    "service": {
                        "protocols": list(self.protocols.values()),
                        "endpoints": endpoints,
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

    def schedule_registration(self):

        query_msg = {"query_records": {"agent_address": self.address}}
        response = self._reg_contract.query(query_msg)

        if response["record"] == []:
            contract_state = self._reg_contract.query({"query_contract_state": {}})
            expiry = contract_state.get("state").get("expiry_height")
            return expiry * BLOCK_INTERVAL

        expiry = response.get("record")[0].get("expiry")
        height = response.get("height")

        return (expiry - height) * BLOCK_INTERVAL

    def get_registration_sequence(self) -> int:
        query_msg = {"query_sequence": {"agent_address": self.address}}
        sequence = self._reg_contract.query(query_msg)["sequence"]

        return sequence

    def on_interval(
        self, period: float, messages: Optional[Union[Model, Set[Model]]] = None
    ):
        return self._protocol.on_interval(period, messages)

    def on_query(
        self,
        model: Model,
        replies: Optional[Union[Model, Set[Model]]] = None,
    ):
        return self._protocol.on_query(model, replies)

    def on_message(
        self,
        model: Model,
        replies: Optional[Union[Model, Set[Model]]] = None,
        allow_unverified: Optional[bool] = False,
    ):
        return self._protocol.on_message(model, replies, allow_unverified)

    def on_event(self, event_type: str) -> EventCallback:
        def decorator_on_event(func: EventCallback) -> EventCallback:
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._add_event_handler(event_type, func)

            return handler

        return decorator_on_event

    def _add_event_handler(
        self,
        event_type: str,
        func: EventCallback,
    ) -> None:
        if event_type == "startup":
            self._on_startup.append(func)
        elif event_type == "shutdown":
            self._on_shutdown.append(func)

    def include(self, protocol: Protocol):
        for func, period in protocol.intervals:
            task = self._loop.create_task(_run_interval(func, self._ctx, period))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        self._interval_messages.update(protocol.interval_messages)

        for schema_digest in protocol.models:
            if schema_digest in self._models:
                raise RuntimeError("Unable to register duplicate model")
            if schema_digest in self._signed_message_handlers:
                raise RuntimeError("Unable to register duplicate message handler")
            if schema_digest in protocol.signed_message_handlers:
                self._signed_message_handlers[
                    schema_digest
                ] = protocol.signed_message_handlers[schema_digest]
            elif schema_digest in protocol.unsigned_message_handlers:
                self._unsigned_message_handlers[
                    schema_digest
                ] = protocol.unsigned_message_handlers[schema_digest]
            else:
                raise RuntimeError("Unable to lookup up message handler in protocol")

            self._models[schema_digest] = protocol.models[schema_digest]

            if schema_digest in protocol.replies:
                self._replies[schema_digest] = protocol.replies[schema_digest]

        if protocol.digest is not None:
            self.protocols[protocol.canonical_name] = protocol.digest

    async def handle_message(self, sender, schema_digest: str, message: JsonStr):
        await self._message_queue.put((schema_digest, sender, message))

    async def startup(self):
        for handler in self._on_startup:
            await handler(self._ctx)

    async def shutdown(self):
        for handler in self._on_shutdown:
            await handler(self._ctx)

    def setup(self):
        # register the internal agent protocol
        self.include(self._protocol)

        # start the background message queue processor
        task = self._loop.create_task(self._process_message_queue())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # start the contract registration update loop
        self._loop.create_task(
            _run_interval(self.register, self._ctx, self.schedule_registration())
        )

    def run(self):
        self.setup()
        self._loop.run_until_complete(self.startup())
        try:
            self._loop.run_until_complete(self._server.serve())
        finally:
            self._loop.run_until_complete(self.shutdown())

    async def _process_message_queue(self):
        while True:
            # get an element from the queue
            schema_digest, sender, message = await self._message_queue.get()

            # lookup the model definition
            model_class: Model = self._models.get(schema_digest)
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
                self._queries,
                replies=self._replies,
                interval_messages=self._interval_messages,
                message_received=MsgDigest(
                    message=message, schema_digest=schema_digest
                ),
            )

            # attempt to find the handler
            handler: MessageCallback = self._unsigned_message_handlers.get(
                schema_digest
            )
            if handler is None:
                if not is_user_address(sender):
                    handler = self._signed_message_handlers.get(schema_digest)
                elif schema_digest in self._signed_message_handlers:
                    await _handle_error(
                        context,
                        sender,
                        ErrorMessage(
                            error="Message must be sent from verified agent address"
                        ),
                    )
                    continue

            if handler is not None:
                await handler(context, sender, recovered)


class Bureau:
    def __init__(self, port: Optional[int] = None):
        self._loop = asyncio.get_event_loop_policy().get_event_loop()
        self._agents = []
        self._port = port or 8000
        self._queries: Dict[str, asyncio.Future] = {}
        self._server = ASGIServer(self._port, self._loop, self._queries)

    def add(self, agent: Agent):
        agent.update_loop(self._loop)
        agent.update_queries(self._queries)
        self._agents.append(agent)

    def run(self):
        for agent in self._agents:
            agent.setup()
        self._loop.run_until_complete(self._server.serve())
