import asyncio
import functools
from typing import Dict, List, Optional, Set, Union, Type, Tuple, Any

from cosmpy.aerial.wallet import LocalWallet, PrivateKey
from cosmpy.crypto.address import Address

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
from uagents.network import get_ledger, get_reg_contract, wait_for_tx_to_complete
from uagents.mailbox import MailboxClient
from uagents.config import (
    REGISTRATION_FEE,
    REGISTRATION_DENOM,
    LEDGER_PREFIX,
    BLOCK_INTERVAL,
    parse_endpoint_config,
    parse_mailbox_config,
    get_logger,
)


async def _run_interval(func: IntervalCallback, ctx: Context, period: float):
    while True:
        try:
            await func(ctx)
        except OSError:
            ctx.logger.exception("OS Error in interval handler")
        except RuntimeError:
            ctx.logger.exception("Runtime Error in interval handler")

        await asyncio.sleep(period)


async def _handle_error(ctx: Context, destination: str, msg: ErrorMessage):
    await ctx.send(destination, msg)


class Agent(Sink):
    def __init__(
        self,
        name: Optional[str] = None,
        port: Optional[int] = None,
        seed: Optional[str] = None,
        endpoint: Optional[Union[str, List[str], Dict[str, dict]]] = None,
        mailbox: Optional[Union[str, Dict[str, str]]] = None,
        resolve: Optional[Resolver] = None,
        version: Optional[str] = None,
    ):
        self._name = name
        self._port = port if port is not None else 8000
        self._background_tasks: Set[asyncio.Task] = set()
        self._resolver = resolve if resolve is not None else AlmanacResolver()
        self._loop = asyncio.get_event_loop_policy().get_event_loop()

        # initialize wallet and identity
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
        if name is None:
            self._name = self.address[0:16]
        self._logger = get_logger(self.name)

        # configure endpoints and mailbox
        self._endpoints = parse_endpoint_config(endpoint)
        self._use_mailbox = mailbox is not None
        if self._use_mailbox:
            self._mailbox = parse_mailbox_config(mailbox)
            self._mailbox_client = MailboxClient(self, self._logger)
            # if mailbox is provided, override endpoints with mailbox endpoint
            self._endpoints = [
                {
                    "url": f"{self.mailbox['http_prefix']}://{self.mailbox['base_url']}/v1/submit",
                    "weight": 1,
                }
            ]
        else:
            self._mailbox = None
            self._mailbox_client = None

        self._ledger = get_ledger()
        self._reg_contract = get_reg_contract()
        self._storage = KeyValueStore(self.address[0:16])
        self._interval_handlers: List[Tuple[IntervalCallback, float]] = []
        self._interval_messages: Set[str] = set()
        self._signed_message_handlers: Dict[str, MessageCallback] = {}
        self._unsigned_message_handlers: Dict[str, MessageCallback] = {}
        self._models: Dict[str, Type[Model]] = {}
        self._replies: Dict[str, Set[Type[Model]]] = {}
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
            logger=self._logger,
        )
        self._dispatcher = dispatcher
        self._message_queue = asyncio.Queue()
        self._on_startup = []
        self._on_shutdown = []
        self._version = version or "0.1.0"

        # initialize the internal agent protocol
        self._protocol = Protocol(name=self._name, version=self._version)

        # keep track of supported protocols
        self.protocols: Dict[str, Protocol] = {}

        # register with the dispatcher
        self._dispatcher.register(self.address, self)

        if not self._use_mailbox:
            self._server = ASGIServer(
                self._port, self._loop, self._queries, logger=self._logger
            )

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._identity.address

    @property
    def wallet(self) -> LocalWallet:
        return self._wallet

    @property
    def storage(self) -> KeyValueStore:
        return self._storage

    @property
    def mailbox(self) -> Dict[str, str]:
        return self._mailbox

    @property
    def mailbox_client(self) -> MailboxClient:
        return self._mailbox_client

    @mailbox.setter
    def mailbox(self, config: Union[str, Dict[str, str]]):
        self._mailbox = parse_mailbox_config(config)

    def sign(self, data: bytes) -> str:
        return self._identity.sign(data)

    def sign_digest(self, digest: bytes) -> str:
        return self._identity.sign_digest(digest)

    def sign_registration(self) -> str:
        assert self._reg_contract.address is not None
        return self._identity.sign_registration(
            str(self._reg_contract.address), self.get_registration_sequence()
        )

    def update_endpoints(self, endpoints: List[Dict[str, Any]]):
        self._endpoints = endpoints

    def update_loop(self, loop):
        self._loop = loop

    def update_queries(self, queries):
        self._queries = queries

    async def _register(self, ctx: Context):
        agent_balance = ctx.ledger.query_bank_balance(Address(ctx.wallet.address()))

        if agent_balance < REGISTRATION_FEE:
            self._logger.warning(
                f"I do not have enough funds to register on Almanac contract\
                    \nFund using wallet address: {self.wallet.address()}"
            )
            return

        signature = self.sign_registration()

        msg = {
            "register": {
                "record": {
                    "service": {
                        "protocols": list(
                            map(lambda x: x.digest, self.protocols.values())
                        ),
                        "endpoints": self._endpoints,
                    }
                },
                "signature": signature,
                "sequence": self.get_registration_sequence(),
                "agent_address": self.address,
            }
        }

        self._logger.info("Registering on Almanac contract...")
        transaction = self._reg_contract.execute(
            msg,
            ctx.wallet,
            funds=f"{REGISTRATION_FEE}{REGISTRATION_DENOM}",
        )
        await wait_for_tx_to_complete(transaction.tx_hash)
        self._logger.info("Registering on Almanac contract...complete")

    def _schedule_registration(self):
        query_msg = {"query_records": {"agent_address": self.address}}
        response = self._reg_contract.query(query_msg)

        if not response["record"]:
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
        self,
        period: float,
        messages: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
    ):
        return self._protocol.on_interval(period, messages)

    def on_query(
        self,
        model: Type[Model],
        replies: Optional[Union[Model, Set[Model]]] = None,
    ):
        return self._protocol.on_query(model, replies)

    def on_message(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        allow_unverified: Optional[bool] = False,
    ):
        return self._protocol.on_message(model, replies, allow_unverified)

    def on_event(self, event_type: str):
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
            self._interval_handlers.append((func, period))

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
            self.protocols[protocol.digest] = protocol

    async def handle_message(self, sender, schema_digest: str, message: JsonStr):
        await self._message_queue.put((schema_digest, sender, message))

    async def _startup(self):
        for handler in self._on_startup:
            await handler(self._ctx)

    async def _shutdown(self):
        for handler in self._on_shutdown:
            await handler(self._ctx)

    def setup(self):
        # register the internal agent protocol
        self.include(self._protocol)
        self._loop.run_until_complete(self._startup())
        if self._endpoints is None:
            self._logger.warning(
                "I have no endpoint and won't be able to receive external messages"
            )
        self.start_background_tasks()

    def start_background_tasks(self):
        # Start the interval tasks
        for func, period in self._interval_handlers:
            task = self._loop.create_task(_run_interval(func, self._ctx, period))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        # start the background message queue processor
        task = self._loop.create_task(self._process_message_queue())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # start the contract registration update loop
        if self._endpoints is not None:
            self._loop.create_task(
                _run_interval(self._register, self._ctx, self._schedule_registration())
            )

    def run(self):
        self.setup()
        try:
            if self._use_mailbox:
                self._loop.create_task(self._mailbox_client.process_deletion_queue())
                self._loop.run_until_complete(self._mailbox_client.run())
            else:
                self._loop.run_until_complete(self._server.serve())
        finally:
            self._loop.run_until_complete(self._shutdown())

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
                logger=self._logger,
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
    def __init__(
        self,
        port: Optional[int] = None,
        endpoint: Optional[Union[str, List[str], Dict[str, dict]]] = None,
    ):
        self._loop = asyncio.get_event_loop_policy().get_event_loop()
        self._agents = []
        self._endpoints = parse_endpoint_config(endpoint)
        self._port = port or 8000
        self._queries: Dict[str, asyncio.Future] = {}
        self._logger = get_logger("bureau")
        self._server = ASGIServer(self._port, self._loop, self._queries, self._logger)
        self._use_mailbox = False

    def add(self, agent: Agent):
        agent.update_loop(self._loop)
        agent.update_queries(self._queries)
        if agent.mailbox is not None:
            self._use_mailbox = True
        else:
            agent.update_endpoints(self._endpoints)
        self._agents.append(agent)

    def run(self):
        tasks = []
        for agent in self._agents:
            agent.setup()
            if agent.mailbox is not None:
                tasks.append(
                    self._loop.create_task(
                        agent.mailbox_client.process_deletion_queue()
                    )
                )
                tasks.append(self._loop.create_task(agent.mailbox_client.run()))
        if not self._use_mailbox:
            tasks.append(self._loop.create_task(self._server.serve()))

        self._loop.run_until_complete(asyncio.gather(*tasks))
