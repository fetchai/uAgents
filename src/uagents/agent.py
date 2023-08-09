"""Agent"""

import asyncio
import functools
from typing import Dict, List, Optional, Set, Union, Type, Tuple, Any, Coroutine
import uuid
import requests

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
from uagents.resolver import Resolver, GlobalResolver
from uagents.storage import KeyValueStore, get_or_create_private_keys
from uagents.network import (
    get_ledger,
    get_almanac_contract,
)
from uagents.mailbox import MailboxClient
from uagents.config import (
    REGISTRATION_FEE,
    MIN_REGISTRATION_TIME,
    LEDGER_PREFIX,
    parse_endpoint_config,
    parse_agentverse_config,
    get_logger,
)


async def _run_interval(func: IntervalCallback, ctx: Context, period: float):
    """
    Run the provided interval callback function at a specified period.

    Args:
        func (IntervalCallback): The interval callback function to run.
        ctx (Context): The context for the agent.
        period (float): The time period at which to run the callback function.
    """
    while True:
        try:
            await func(ctx)
        except OSError:
            ctx.logger.exception("OS Error in interval handler")
        except RuntimeError:
            ctx.logger.exception("Runtime Error in interval handler")

        await asyncio.sleep(period)


async def _delay(coroutine: Coroutine, delay_seconds: float):
    """
    Delay the execution of the provided coroutine by the specified number of seconds.

    Args:
        coroutine (Coroutine): The coroutine to delay.
        delay_seconds (float): The delay time in seconds.
    """
    await asyncio.sleep(delay_seconds)
    await coroutine


async def _handle_error(ctx: Context, destination: str, msg: ErrorMessage):
    """
    Handle an error message by sending it to the specified destination.

    Args:
        ctx (Context): The context for the agent.
        destination (str): The destination address to send the error message to.
        msg (ErrorMessage): The error message to handle.
    """
    await ctx.send(destination, msg)


class Agent(Sink):
    """
    An agent that interacts within a communication environment.

    Attributes:
        _name (str): The name of the agent.
        _port (int): The port on which the agent runs.
        _background_tasks (Set[asyncio.Task]): Set of background tasks associated with the agent.
        _resolver (Resolver): The resolver for agent communication.
        _loop (asyncio.AbstractEventLoop): The asyncio event loop used by the agent.
        _logger: The logger instance for logging agent activities.
        _endpoints (List[dict]): List of communication endpoints.
        _use_mailbox (bool): Indicates if the agent uses a mailbox for communication.
        _agentverse (dict): Agentverse configuration settings.
        _mailbox_client (MailboxClient): Client for interacting with the mailbox.
        _ledger: The ledger for recording agent transactions.
        _almanac_contract: The almanac contract for agent metadata.
        _storage: Key-value store for agent data storage.
        _interval_handlers (List[Tuple[IntervalCallback, float]]): List of interval
        handlers and their periods.
        _interval_messages (Set[str]): Set of interval message names.
        _signed_message_handlers (Dict[str, MessageCallback]): Handlers for signed messages.
        _unsigned_message_handlers (Dict[str, MessageCallback]): Handlers for
        unsigned messages.
        _models (Dict[str, Type[Model]]): Dictionary of supported data models.
        _replies (Dict[str, Set[Type[Model]]]): Dictionary of reply data models.
        _queries (Dict[str, asyncio.Future]): Dictionary of active queries.
        _dispatcher: The dispatcher for message handling.
        _message_queue: Asynchronous queue for incoming messages.
        _on_startup (List[Callable]): List of functions to run on agent startup.
        _on_shutdown (List[Callable]): List of functions to run on agent shutdown.
        _version (str): The version of the agent.
        _protocol (Protocol): The internal agent protocol.
        protocols (Dict[str, Protocol]): Dictionary of supported protocols.
        _ctx (Context): The context for agent interactions.

    Methods:
        __init__: Initialize the Agent instance.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        port: Optional[int] = None,
        seed: Optional[str] = None,
        endpoint: Optional[Union[str, List[str], Dict[str, dict]]] = None,
        agentverse: Optional[Union[str, Dict[str, str]]] = None,
        mailbox: Optional[Union[str, Dict[str, str]]] = None,
        resolve: Optional[Resolver] = None,
        version: Optional[str] = None,
    ):
        """
        Initialize an Agent instance.

        Args:
            name (Optional[str]): The name of the agent.
            port (Optional[int]): The port on which the agent will run.
            seed (Optional[str]): The seed for generating keys.
            endpoint (Optional[Union[str, List[str], Dict[str, dict]]]): The endpoint configuration.
            agentverse (Optional[Union[str, Dict[str, str]]]): The agentverse configuration.
            mailbox (Optional[Union[str, Dict[str, str]]]): The mailbox configuration.
            resolve (Optional[Resolver]): The resolver to use for agent communication.
            version (Optional[str]): The version of the agent.
        """
        self._name = name
        self._port = port if port is not None else 8000
        self._background_tasks: Set[asyncio.Task] = set()
        self._resolver = resolve if resolve is not None else GlobalResolver()
        self._loop = asyncio.get_event_loop_policy().get_event_loop()

        self._initialize_wallet_and_identity(seed, name)

        self._logger = get_logger(self.name)

        # configure endpoints and mailbox
        self._endpoints = parse_endpoint_config(endpoint)
        self._use_mailbox = False

        if mailbox:
            # agentverse config overrides mailbox config
            # but mailbox is kept for backwards compatibility
            if agentverse:
                self._logger.warning(
                    "Ignoring the provided 'mailbox' configuration since 'agentverse' overrides it"
                )
            else:
                agentverse = mailbox
            self._logger.warning(
                "The 'mailbox' configuration is deprecated in favor of 'agentverse'"
            )
        self._agentverse = parse_agentverse_config(agentverse)
        self._use_mailbox = self._agentverse["use_mailbox"]
        if self._use_mailbox:
            self._mailbox_client = MailboxClient(self, self._logger)
            # if mailbox is provided, override endpoints with mailbox endpoint
            self._endpoints = [
                {
                    "url": f"{self.mailbox['http_prefix']}://{self.mailbox['base_url']}/v1/submit",
                    "weight": 1,
                }
            ]
        else:
            self._mailbox_client = None

        self._ledger = get_ledger()
        self._almanac_contract = get_almanac_contract()
        self._storage = KeyValueStore(self.address[0:16])
        self._interval_handlers: List[Tuple[IntervalCallback, float]] = []
        self._interval_messages: Set[str] = set()
        self._signed_message_handlers: Dict[str, MessageCallback] = {}
        self._unsigned_message_handlers: Dict[str, MessageCallback] = {}
        self._models: Dict[str, Type[Model]] = {}
        self._replies: Dict[str, Set[Type[Model]]] = {}
        self._queries: Dict[str, asyncio.Future] = {}
        self._dispatcher = dispatcher
        self._message_queue = asyncio.Queue()
        self._on_startup = []
        self._on_shutdown = []
        self._version = version or "0.1.0"

        # initialize the internal agent protocol
        self._protocol = Protocol(name=self._name, version=self._version)

        # keep track of supported protocols
        self.protocols: Dict[str, Protocol] = {}

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
            protocols=self.protocols,
            logger=self._logger,
        )

        # register with the dispatcher
        self._dispatcher.register(self.address, self)

        if not self._use_mailbox:
            self._server = ASGIServer(
                self._port, self._loop, self._queries, logger=self._logger
            )

    def _initialize_wallet_and_identity(self, seed, name):
        """
        Initialize the wallet and identity for the agent.

        If seed is provided, the identity and wallet are derived from the seed.
        If seed is not provided, they are either generated or fetched based on the provided name.

        Args:
            seed (str or None): The seed for generating keys.
            name (str or None): The name of the agent.
        """
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

    @property
    def name(self) -> str:
        """
        Get the name of the agent.

        Returns:
            str: The name of the agent.
        """
        return self._name

    @property
    def address(self) -> str:
        """
        Get the address of the agent's identity.

        Returns:
            str: The address of the agent's identity.
        """
        return self._identity.address

    @property
    def wallet(self) -> LocalWallet:
        """
        Get the wallet of the agent.

        Returns:
            LocalWallet: The agent's wallet.
        """
        return self._wallet

    @property
    def storage(self) -> KeyValueStore:
        """
        Get the key-value store used by the agent for data storage.

        Returns:
            KeyValueStore: The key-value store instance.
        """
        return self._storage

    @property
    def mailbox(self) -> Dict[str, str]:
        """
        Get the mailbox configuration of the agent.

        Returns:
            Dict[str, str]: The mailbox configuration.
        """
        return self._agentverse

    @property
    def agentverse(self) -> Dict[str, str]:
        """
        Get the agentverse configuration of the agent.

        Returns:
            Dict[str, str]: The agentverse configuration.
        """
        return self._agentverse

    @property
    def mailbox_client(self) -> MailboxClient:
        """
        Get the mailbox client used by the agent for mailbox communication.

        Returns:
            MailboxClient: The mailbox client instance.
        """
        return self._mailbox_client

    @mailbox.setter
    def mailbox(self, config: Union[str, Dict[str, str]]):
        """
        Set the mailbox configuration for the agent.

        Args:
            config (Union[str, Dict[str, str]]): The new mailbox configuration.
        """
        self._agentverse = parse_agentverse_config(config)

    @agentverse.setter
    def agentverse(self, config: Union[str, Dict[str, str]]):
        """
        Set the agentverse configuration for the agent.

        Args:
            config (Union[str, Dict[str, str]]): The new agentverse configuration.
        """
        self._agentverse = parse_agentverse_config(config)

    def sign(self, data: bytes) -> str:
        """
        Sign the provided data.

        Args:
            data (bytes): The data to be signed.

        Returns:
            str: The signature of the data.

        """
        return self._identity.sign(data)

    def sign_digest(self, digest: bytes) -> str:
        """
        Sign the provided digest.

        Args:
            digest (bytes): The digest to be signed.

        Returns:
            str: The signature of the digest.

        """
        return self._identity.sign_digest(digest)

    def sign_registration(self) -> str:
        """
        Sign the registration data for Almanac contract.

        Returns:
            str: The signature of the registration data.

        Raises:
            AssertionError: If the Almanac contract address is None.

        """
        assert self._almanac_contract.address is not None
        return self._identity.sign_registration(
            str(self._almanac_contract.address),
            self._almanac_contract.get_sequence(self.address),
        )

    def update_endpoints(self, endpoints: List[Dict[str, Any]]):
        """
        Update the list of endpoints.

        Args:
            endpoints (List[Dict[str, Any]]): List of endpoint dictionaries.

        """

        self._endpoints = endpoints

    def update_loop(self, loop):
        """
        Update the event loop.

        Args:
            loop: The event loop.

        """

        self._loop = loop

    def update_queries(self, queries):
        """
        Update the queries attribute.

        Args:
            queries: The queries attribute.

        """

        self._queries = queries

    async def register(self):
        """
        Register with the Almanac contract.

        This method checks for registration conditions and performs registration
        if necessary.

        """
        if self._endpoints is None:
            self._logger.warning(
                "I have no endpoint and cannot receive external messages"
            )
            return

        # register if not yet registered or registration is about to expire
        # or anything has changed from the last registration
        if (
            not self._almanac_contract.is_registered(self.address)
            or self._schedule_registration() < MIN_REGISTRATION_TIME
            or self._endpoints != self._almanac_contract.get_endpoints(self.address)
            or list(self.protocols.keys())
            != self._almanac_contract.get_protocols(self.address)
        ):
            agent_balance = self._ledger.query_bank_balance(
                Address(self.wallet.address())
            )

            if agent_balance < REGISTRATION_FEE:
                self._logger.warning(
                    f"I do not have enough funds to register on Almanac contract\
                        \nFund using wallet address: {self.wallet.address()}"
                )
                return
            self._logger.info("Registering on almanac contract...")
            signature = self.sign_registration()
            await self._almanac_contract.register(
                self._ledger,
                self.wallet,
                self.address,
                list(self.protocols.keys()),
                self._endpoints,
                signature,
            )
            self._logger.info("Registering on almanac contract...complete")
        else:
            self._logger.info("Almanac registration is up to date!")

    async def _registration_loop(self):
        """
        Execute the registration loop.

        This method registers with the Almanac contract and schedules the next
        registration.

        """

        await self.register()
        # schedule the next registration
        self._loop.create_task(
            _delay(self._registration_loop(), self._schedule_registration())
        )

    def _schedule_registration(self):
        """
        Get the scheduled registration expiry for the agent.

        Returns:
            Expiry: The scheduled registration expiry.

        """

        return self._almanac_contract.get_expiry(self.address)

    def on_interval(
        self,
        period: float,
        messages: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
    ):
        """
        Set up an interval event with a callback.

        Args:
            period (float): The interval period.
            messages (Optional[Union[Type[Model], Set[Type[Model]]]]): Optional message types.

        Returns:
            Callable: The callback function for the interval event.

        """

        return self._protocol.on_interval(period, messages)

    def on_query(
        self,
        model: Type[Model],
        replies: Optional[Union[Model, Set[Model]]] = None,
    ):
        """
        Set up a query event with a callback.

        Args:
            model (Type[Model]): The query model.
            replies (Optional[Union[Model, Set[Model]]]): Optional reply models.

        Returns:
            Callable: The callback function for the query event.

        """

        return self._protocol.on_query(model, replies)

    def on_message(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        allow_unverified: Optional[bool] = False,
    ):
        """
        Set up a message event with a callback.

        Args:
            model (Type[Model]): The message model.
            replies (Optional[Union[Type[Model], Set[Type[Model]]]]): Optional reply models.
            allow_unverified (Optional[bool]): Allow unverified messages.

        Returns:
            Callable: The callback function for the message event.

        """

        return self._protocol.on_message(model, replies, allow_unverified)

    def on_event(self, event_type: str):
        """
        Decorator to register an event handler for a specific event type.

        Args:
            event_type (str): The type of event.

        Returns:
            Callable: The decorator function for registering event handlers.

        """

        def decorator_on_event(func: EventCallback) -> EventCallback:
            """
            Decorator function to register an event handler for a specific event type.

            Args:
                func (EventCallback): The event handler function.

            Returns:
                EventCallback: The decorated event handler function.

            """

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
        """
        Add an event handler function to the specified event type.

        Args:
            event_type (str): The type of event.
            func (EventCallback): The event handler function.

        """

        if event_type == "startup":
            self._on_startup.append(func)
        elif event_type == "shutdown":
            self._on_shutdown.append(func)

    def include(self, protocol: Protocol, publish_manifest: Optional[bool] = False):
        """
        Include a protocol into the agent's capabilities.

        Args:
            protocol (Protocol): The protocol to include.
            publish_manifest (Optional[bool]): Flag to publish the protocol's manifest.

        Raises:
            RuntimeError: If a duplicate model, signed message handler, or message handler
            is encountered.

        """
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

        if publish_manifest:
            self.publish_manifest(protocol.manifest())

    def publish_manifest(self, manifest: Dict[str, Any]):
        """
        Publish a protocol manifest to the Almanac.

        Args:
            manifest (Dict[str, Any]): The protocol manifest.

        """
        try:
            resp = requests.post(
                f"{self._agentverse['http_prefix']}://{self._agentverse['base_url']}"
                + "/v1/almanac/manifests",
                json=manifest,
                timeout=5,
            )
            if resp.status_code == 200:
                self._logger.info(
                    f"Manifest published successfully: {manifest['metadata']['name']}"
                )
            else:
                self._logger.warning(f"Unable to publish manifest: {resp.text}")
        except requests.exceptions.RequestException as ex:
            self._logger.warning(f"Unable to publish manifest: {ex}")

    async def handle_message(
        self, sender, schema_digest: str, message: JsonStr, session: uuid.UUID
    ):
        """
        Handle an incoming message asynchronously.

        Args:
            sender: The sender of the message.
            schema_digest (str): The schema digest of the message.
            message (JsonStr): The message content in JSON format.
            session (uuid.UUID): The session UUID.

        """
        await self._message_queue.put((schema_digest, sender, message, session))

    async def _startup(self):
        """
        Perform startup actions asynchronously.

        """
        await self._registration_loop()
        for handler in self._on_startup:
            await handler(self._ctx)

    async def _shutdown(self):
        """
        Perform shutdown actions asynchronously.

        """
        for handler in self._on_shutdown:
            await handler(self._ctx)

    def setup(self):
        """
        Set up the agent.

        """
        # register the internal agent protocol
        self.include(self._protocol)
        self._loop.run_until_complete(self._startup())
        if self._endpoints is None:
            self._logger.warning(
                "I have no endpoint and won't be able to receive external messages"
            )
        self.start_background_tasks()

    def start_background_tasks(self):
        """
        Start background tasks for the agent.

        """
        # Start the interval tasks
        for func, period in self._interval_handlers:
            task = self._loop.create_task(_run_interval(func, self._ctx, period))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        # start the background message queue processor
        task = self._loop.create_task(self._process_message_queue())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def run(self):
        """
        Run the agent.

        """
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
        """
        Process the message queue asynchronously.

        """
        while True:
            # get an element from the queue
            schema_digest, sender, message, session = await self._message_queue.get()

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
                session=session,
                replies=self._replies,
                interval_messages=self._interval_messages,
                message_received=MsgDigest(
                    message=message, schema_digest=schema_digest
                ),
                protocols=self.protocols,
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
    """
    A class representing a Bureau of agents.

    This class manages a collection of agents and orchestrates their execution.

    Args:
        port (Optional[int]): The port number for the server.
        endpoint (Optional[Union[str, List[str], Dict[str, dict]]]): Configuration
        for agent endpoints.

    Attributes:
        _loop (asyncio.AbstractEventLoop): The event loop.
        _agents (List[Agent]): A list of Agent instances within the bureau.
        _endpoints (List[Dict[str, Any]]): A list of endpoint dictionaries for the agents.
        _port (int): The port number for the server.
        _queries (Dict[str, asyncio.Future]): A dictionary of query identifiers to asyncio futures.
        _logger (Logger): The logger instance.
        _server (ASGIServer): The ASGI server instance for handling requests.
        _use_mailbox (bool): A flag indicating whether mailbox functionality is enabled.

    """
    def __init__(
        self,
        port: Optional[int] = None,
        endpoint: Optional[Union[str, List[str], Dict[str, dict]]] = None,
    ):
        """
        Initialize a Bureau instance.

        Args:
            port (Optional[int]): The port number for the server.
            endpoint (Optional[Union[str, List[str], Dict[str, dict]]]): Configuration
            for agent endpoints.
        """
        self._loop = asyncio.get_event_loop_policy().get_event_loop()
        self._agents: List[Agent] = []
        self._endpoints = parse_endpoint_config(endpoint)
        self._port = port or 8000
        self._queries: Dict[str, asyncio.Future] = {}
        self._logger = get_logger("bureau")
        self._server = ASGIServer(self._port, self._loop, self._queries, self._logger)
        self._use_mailbox = False

    def add(self, agent: Agent):
        """
        Add an agent to the bureau.

        Args:
            agent (Agent): The agent instance to be added.

        """
        agent.update_loop(self._loop)
        agent.update_queries(self._queries)
        if agent.agentverse["use_mailbox"]:
            self._use_mailbox = True
        else:
            agent.update_endpoints(self._endpoints)
        self._agents.append(agent)

    def run(self):
        """
        Run the agents managed by the bureau.

        """
        tasks = []
        for agent in self._agents:
            agent.setup()
            if agent.agentverse["use_mailbox"]:
                tasks.append(
                    self._loop.create_task(
                        agent.mailbox_client.process_deletion_queue()
                    )
                )
                tasks.append(self._loop.create_task(agent.mailbox_client.run()))
        if not self._use_mailbox:
            tasks.append(self._loop.create_task(self._server.serve()))

        self._loop.run_until_complete(asyncio.gather(*tasks))
