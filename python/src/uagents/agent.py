"""Agent"""

import asyncio
import contextlib
import functools
import logging
import uuid
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

import requests
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import LocalWallet, PrivateKey
from cosmpy.crypto.address import Address
from pydantic import ValidationError

from uagents.asgi import ASGIServer
from uagents.communication import Dispenser
from uagents.config import (
    AVERAGE_BLOCK_INTERVAL,
    LEDGER_PREFIX,
    MAINNET_PREFIX,
    REGISTRATION_RETRY_INTERVAL_SECONDS,
    REGISTRATION_UPDATE_INTERVAL_SECONDS,
    TESTNET_PREFIX,
    AgentverseConfig,
    parse_agentverse_config,
    parse_endpoint_config,
)
from uagents.context import Context, ContextFactory, ExternalContext, InternalContext
from uagents.crypto import Identity, derive_key_from_seed, is_user_address
from uagents.dispatch import Sink, dispatcher
from uagents.envelope import EnvelopeHistory, EnvelopeHistoryEntry
from uagents.mailbox import (
    AgentverseConnectRequest,
    MailboxClient,
    RegistrationResponse,
    is_mailbox_agent,
    register_in_agentverse,
)
from uagents.models import ErrorMessage, Model
from uagents.network import (
    InsufficientFundsError,
    get_almanac_contract,
    get_ledger,
)
from uagents.protocol import Protocol
from uagents.registration import (
    AgentRegistrationPolicy,
    AgentStatusUpdate,
    BatchLedgerRegistrationPolicy,
    BatchRegistrationPolicy,
    DefaultBatchRegistrationPolicy,
    DefaultRegistrationPolicy,
    LedgerBasedRegistrationPolicy,
    update_agent_status,
)
from uagents.resolver import GlobalResolver, Resolver
from uagents.storage import KeyValueStore, get_or_create_private_keys
from uagents.types import (
    AgentEndpoint,
    AgentInfo,
    AgentMetadata,
    EventCallback,
    IntervalCallback,
    JsonStr,
    MessageCallback,
    MsgDigest,
    RestGetHandler,
    RestHandler,
    RestHandlerMap,
    RestMethod,
    RestPostHandler,
)
from uagents.utils import get_logger


async def _run_interval(
    func: IntervalCallback,
    logger: logging.Logger,
    context_factory: ContextFactory,
    period: float,
):
    """
    Run the provided interval callback function at a specified period.

    Args:
        func (IntervalCallback): The interval callback function to run.
        logger (logging.Logger): The logger instance for logging interval handler activities.
        context_factory (ContextFactory): The factory function for creating the context.
        period (float): The time period at which to run the callback function.
    """
    while True:
        try:
            ctx = context_factory()
            await func(ctx)
        except OSError as ex:
            logger.exception(f"OS Error in interval handler: {ex}")
        except RuntimeError as ex:
            logger.exception(f"Runtime Error in interval handler: {ex}")
        except Exception as ex:
            logger.exception(f"Exception in interval handler: {ex}")

        await asyncio.sleep(period)


async def _send_error_message(ctx: Context, destination: str, msg: ErrorMessage):
    """
    Send an error message to the specified destination.

    Args:
        ctx (Context): The context for the agent.
        destination (str): The destination address to send the error message to.
        msg (ErrorMessage): The error message to send.
    """
    await ctx.send(destination, msg)


class AgentRepresentation:
    """
    Represents an agent in the context of a message.

    Attributes:
        _address (str): The address of the agent.
        _name (Optional[str]): The name of the agent.
        _signing_callback (Callable): The callback for signing messages.

    Properties:
        name (str): The name of the agent.
        address (str): The address of the agent.
        identifier (str): The agent's address and network prefix.

    Methods:
        sign_digest(data: bytes) -> str: Sign the provided data with the agent's identity.
    """

    def __init__(
        self,
        address: str,
        name: Optional[str],
        signing_callback: Callable,
    ):
        """
        Initialize the AgentRepresentation instance.

        Args:
            address (str): The address of the context.
            name (Optional[str]): The optional name associated with the context.
            signing_callback (Callable): The callback for signing messages.
        """
        self._address = address
        self._name = name
        self._signing_callback = signing_callback

    @property
    def name(self) -> str:
        """
        Get the name associated with the context or a truncated address if name is None.

        Returns:
            str: The name or truncated address.
        """
        if self._name is not None:
            return self._name
        return self._address[:10]

    @property
    def address(self) -> str:
        """
        Get the address of the context.

        Returns:
            str: The address of the context.
        """
        return self._address

    @property
    def identifier(self) -> str:
        """
        Get the address of the agent used for communication including the network prefix.

        Returns:
            str: The agent's address and network prefix.
        """
        return TESTNET_PREFIX + "://" + self._address

    def sign_digest(self, data: bytes) -> str:
        """
        Sign the provided data with the callback of the agent's identity.

        Args:
            data (bytes): The data to sign.

        Returns:
            str: The signature of the data.
        """
        return self._signing_callback(data)


class Agent(Sink):
    """
    An agent that interacts within a communication environment.

    Attributes:
        _name (str): The name of the agent.
        _port (int): The port on which the agent's server runs.
        _background_tasks (Set[asyncio.Task]): Set of background tasks associated with the agent.
        _resolver (Resolver): The resolver for agent communication.
        _loop (asyncio.AbstractEventLoop): The asyncio event loop used by the agent.
        _logger: The logger instance for logging agent activities.
        _endpoints (List[AgentEndpoint]): List of endpoints at which the agent is reachable.
        _use_mailbox (bool): Indicates if the agent uses a mailbox for communication.
        _agentverse (AgentverseConfig): Agentverse configuration settings.
        _mailbox_client (MailboxClient): The client for interacting with the agentverse mailbox.
        _ledger: The client for interacting with the blockchain ledger.
        _almanac_contract: The almanac contract for registering agent addresses to endpoints.
        _storage: Key-value store for agent data storage.
        _interval_handlers (List[Tuple[IntervalCallback, float]]): List of interval
        handlers and their periods.
        _interval_messages (Set[str]): Set of message digests that may be sent by interval tasks.
        _signed_message_handlers (Dict[str, MessageCallback]): Handlers for signed messages.
        _unsigned_message_handlers (Dict[str, MessageCallback]): Handlers for
        unsigned messages.
        _message_cache (EnvelopeHistory): History of messages received by the agent.
        _models (Dict[str, Type[Model]]): Dictionary mapping supported message digests to messages.
        _replies (Dict[str, Dict[str, Type[Model]]]): Dictionary of allowed replies for each type
        of incoming message.
        _queries (Dict[str, asyncio.Future]): Dictionary mapping query senders to their response
        Futures.
        _dispatcher: The dispatcher for internal handling/sorting of messages.
        _dispenser: The dispatcher for external message handling.
        _message_queue: Asynchronous queue for incoming messages.
        _on_startup (List[Callable]): List of functions to run on agent startup.
        _on_shutdown (List[Callable]): List of functions to run on agent shutdown.
        _version (str): The version of the agent.
        _protocol (Protocol): The internal agent protocol consisting of all interval and message
        handlers assigned with agent decorators.
        protocols (Dict[str, Protocol]): Dictionary mapping all supported protocol digests to their
        corresponding protocols.
        _ctx (Context): The context for agent interactions.
        _test (bool): True if the agent will register and transact on the testnet.
        _enable_agent_inspector (bool): Enable the agent inspector REST endpoints.
        _metadata (Dict[str, Any]): Metadata associated with the agent.

    Properties:
        name (str): The name of the agent.
        address (str): The address of the agent used for communication.
        identifier (str): The Agent Identifier, including network prefix and address.
        wallet (LocalWallet): The agent's wallet for transacting on the ledger.
        storage (KeyValueStore): The key-value store for storage operations.
        agentverse (AgentverseConfig): The agentverse configuration for the agent.
        mailbox_client (MailboxClient): The client for interacting with the agentverse mailbox.
        protocols (Dict[str, Protocol]): Dictionary mapping all supported protocol digests to their
        corresponding protocols.
        metadata (Optional[Dict[str, Any]]): Metadata associated with the agent.

    """

    def __init__(
        self,
        name: Optional[str] = None,
        port: Optional[int] = None,
        seed: Optional[str] = None,
        endpoint: Optional[Union[str, List[str], Dict[str, dict]]] = None,
        agentverse: Optional[Union[str, Dict[str, str]]] = None,
        mailbox: bool = False,
        proxy: bool = False,
        resolve: Optional[Resolver] = None,
        registration_policy: Optional[AgentRegistrationPolicy] = None,
        enable_wallet_messaging: Union[bool, Dict[str, str]] = False,
        wallet_key_derivation_index: Optional[int] = 0,
        max_resolver_endpoints: Optional[int] = None,
        version: Optional[str] = None,
        test: bool = True,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        log_level: Union[int, str] = logging.INFO,
        enable_agent_inspector: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an Agent instance.

        Args:
            name (Optional[str]): The name of the agent.
            port (Optional[int]): The port on which the agent's server will run.
            seed (Optional[str]): The seed for generating keys.
            endpoint (Optional[Union[str, List[str], Dict[str, dict]]]): The endpoint configuration.
            agentverse (Optional[Union[str, Dict[str, str]]]): The agentverse configuration.
            mailbox (bool): True if the agent will receive messages via an Agentverse mailbox.
            proxy (bool): True if the agent will receive messages via an Agentverse proxy endpoint.
            resolve (Optional[Resolver]): The resolver to use for agent communication.
            enable_wallet_messaging (Optional[Union[bool, Dict[str, str]]]): Whether to enable
            wallet messaging. If '{"chain_id": CHAIN_ID}' is provided, this sets the chain ID for
            the messaging server.
            wallet_key_derivation_index (Optional[int]): The index used for deriving the wallet key.
            max_resolver_endpoints (Optional[int]): The maximum number of endpoints to resolve.
            version (Optional[str]): The version of the agent.
            test (Optional[bool]): True if the agent will register and transact on the testnet.
            loop (Optional[asyncio.AbstractEventLoop]): The asyncio event loop to use.
            log_level (Union[int, str]): The logging level for the agent.
            enable_agent_inspector (bool): Enable the agent inspector for debugging.
            metadata (Optional[Dict[str, Any]]): Optional metadata to include in the agent object.
        """
        self._init_done = False
        self._name = name
        self._port = port or 8000

        self._loop = loop or asyncio.get_event_loop_policy().get_event_loop()

        # initialize wallet and identity
        self._initialize_wallet_and_identity(seed, name, wallet_key_derivation_index)
        self._logger = get_logger(self.name, level=log_level)

        self._agentverse = parse_agentverse_config(agentverse)

        # configure endpoints and mailbox
        self._endpoints = parse_endpoint_config(
            endpoint, self._agentverse, mailbox, proxy, self._logger
        )

        self._use_mailbox = is_mailbox_agent(self._endpoints, self._agentverse)
        if self._use_mailbox:
            self._mailbox_client = MailboxClient(
                self._identity, self._agentverse, self._logger
            )
        else:
            self._mailbox_client = None

        self._almanac_api_url = f"{self._agentverse.url}/v1/almanac"
        self._resolver = resolve or GlobalResolver(
            max_endpoints=max_resolver_endpoints,
            almanac_api_url=self._almanac_api_url,
        )

        self._ledger = get_ledger(test)
        self._almanac_contract = get_almanac_contract(test)
        self._storage = KeyValueStore(self.address[0:16])
        self._interval_handlers: List[Tuple[IntervalCallback, float]] = []
        self._interval_messages: Set[str] = set()
        self._signed_message_handlers: Dict[str, MessageCallback] = {}
        self._unsigned_message_handlers: Dict[str, MessageCallback] = {}
        self._message_cache: EnvelopeHistory = EnvelopeHistory(envelopes=[])
        self._rest_handlers: RestHandlerMap = {}
        self._models: Dict[str, Type[Model]] = {}
        self._replies: Dict[str, Dict[str, Type[Model]]] = {}
        self._queries: Dict[str, asyncio.Future] = {}
        self._dispatcher = dispatcher
        self._dispenser = Dispenser(msg_cache_ref=self._message_cache)
        self._message_queue = asyncio.Queue()
        self._on_startup = []
        self._on_shutdown = []
        self._test = test
        self._version = version or "0.1.0"
        self._registration_policy = registration_policy or None

        if self._registration_policy is None:
            self._registration_policy = DefaultRegistrationPolicy(
                self._identity,
                self._ledger,
                self._wallet,
                self._almanac_contract,
                self._test,
                logger=self._logger,
                almanac_api=self._almanac_api_url,
            )
        self._metadata = self._initialize_metadata(metadata)

        self.initialize_wallet_messaging(enable_wallet_messaging)

        # initialize the internal agent protocol
        self._protocol = Protocol(name=self._name, version=self._version)

        # keep track of supported protocols
        self.protocols: Dict[str, Protocol] = {}

        # register with the dispatcher
        self._dispatcher.register(self.address, self)

        self._server = ASGIServer(
            port=self._port,
            loop=self._loop,
            queries=self._queries,
            logger=self._logger,
        )

        # define default error message handler
        @self.on_message(ErrorMessage)
        async def _handle_error_message(ctx: Context, sender: str, msg: ErrorMessage):
            ctx.logger.exception(f"Received error message from {sender}: {msg.error}")

        # define default rest message handlers if agent inspector is enabled
        if enable_agent_inspector:

            @self.on_rest_get("/agent_info", AgentInfo)  # type: ignore
            async def _handle_get_info(_ctx: Context):
                return AgentInfo(
                    agent_address=self.address,
                    endpoints=self._endpoints,
                    protocols=list(self.protocols.keys()),
                    metadata=self.metadata,
                )

            @self.on_rest_get("/messages", EnvelopeHistory)  # type: ignore
            async def _handle_get_messages(_ctx: Context):
                return self._message_cache

            @self.on_rest_post("/prove", AgentverseConnectRequest, RegistrationResponse)
            async def _handle_prove(_ctx: Context, token: AgentverseConnectRequest):
                return await register_in_agentverse(
                    token, self._identity, self._endpoints, self._agentverse
                )

        self._enable_agent_inspector = enable_agent_inspector

        self._init_done = True

    def _build_context(self) -> InternalContext:
        """
        An internal method to build the context for the agent.

        Returns:
            InternalContext: The internal context for the agent.
        """
        return InternalContext(
            agent=AgentRepresentation(
                address=self.address,
                name=self._name,
                signing_callback=self._identity.sign_digest,
            ),
            storage=self._storage,
            ledger=self._ledger,
            resolver=self._resolver,
            dispenser=self._dispenser,
            interval_messages=self._interval_messages,
            wallet_messaging_client=self._wallet_messaging_client,
            logger=self._logger,
        )

    def _initialize_wallet_and_identity(self, seed, name, wallet_key_derivation_index):
        """
        Initialize the wallet and identity for the agent.

        If seed is provided, the identity and wallet are derived from the seed.
        If seed is not provided, they are either generated or fetched based on the provided name.

        Args:
            seed (str or None): The seed for generating keys.
            name (str or None): The name of the agent.
            wallet_key_derivation_index (int): The index for deriving the wallet key.
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
                PrivateKey(
                    derive_key_from_seed(
                        seed, LEDGER_PREFIX, wallet_key_derivation_index
                    )
                ),
                prefix=LEDGER_PREFIX,
            )
        if name is None:
            self._name = self.address[0:16]

    def initialize_wallet_messaging(
        self, enable_wallet_messaging: Union[bool, Dict[str, str]]
    ):
        """
        Initialize wallet messaging for the agent.

        Args:
            enable_wallet_messaging (Union[bool, Dict[str, str]]): Wallet messaging configuration.
        """
        if enable_wallet_messaging:
            wallet_chain_id = self._ledger.network_config.chain_id
            if (
                isinstance(enable_wallet_messaging, dict)
                and "chain_id" in enable_wallet_messaging
            ):
                wallet_chain_id = enable_wallet_messaging["chain_id"]

            try:
                from uagents.wallet_messaging import WalletMessagingClient

                self._wallet_messaging_client = WalletMessagingClient(
                    self._identity,
                    self._wallet,
                    wallet_chain_id,
                    self._logger,
                )
            except ModuleNotFoundError:
                self._logger.exception(
                    "Unable to include wallet messaging. "
                    "Please install the 'wallet' extra to enable wallet messaging."
                )
                self._wallet_messaging_client = None
        else:
            self._wallet_messaging_client = None

    def _initialize_metadata(
        self, metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Initialize the metadata for the agent.

        Args:
            metadata (Optional[Dict[str, Any]]): The metadata to include in the agent object.

        Returns:
            Dict[str, Any]: The filtered metadata.
        """
        if not metadata:
            return {}

        try:
            model = AgentMetadata.model_validate(metadata)
            validated_metadata = model.model_dump(exclude_unset=True)
        except ValidationError as e:
            self._logger.error(e)
            raise RuntimeError("Invalid metadata provided for agent.") from None

        return validated_metadata

    @property
    def name(self) -> str:
        """
        Get the name of the agent.

        Returns:
            str: The name of the agent.
        """
        return self._name or self.address[0:16]

    @property
    def address(self) -> str:
        """
        Get the address of the agent used for communication.

        Returns:
            str: The agent's address.
        """
        return self._identity.address

    @property
    def identifier(self) -> str:
        """
        Get the Agent Identifier, including network prefix and address.

        Returns:
            str: The agent's identifier.
        """
        prefix = TESTNET_PREFIX if self._test else MAINNET_PREFIX
        return prefix + "://" + self._identity.address

    @property
    def wallet(self) -> LocalWallet:
        """
        Get the wallet of the agent.

        Returns:
            LocalWallet: The agent's wallet.
        """
        return self._wallet

    @property
    def ledger(self) -> LedgerClient:
        """
        Get the ledger of the agent.

        Returns:
            LedgerClient: The agent's ledger
        """
        return self._ledger

    @property
    def storage(self) -> KeyValueStore:
        """
        Get the key-value store used by the agent for data storage.

        Returns:
            KeyValueStore: The key-value store instance.
        """
        return self._storage

    @property
    def agentverse(self) -> AgentverseConfig:
        """
        Get the agentverse configuration of the agent.

        Returns:
            Dict[str, str]: The agentverse configuration.
        """
        return self._agentverse

    @property
    def mailbox_client(self) -> Optional[MailboxClient]:
        """
        Get the mailbox client used by the agent for mailbox communication.

        Returns:
            Optional[MailboxClient]: The mailbox client instance.
        """
        return self._mailbox_client

    @property
    def balance(self) -> int:
        """
        Get the balance of the agent.

        Returns:
            int: Bank balance.
        """

        return self.ledger.query_bank_balance(Address(self.wallet.address()))

    @property
    def info(self) -> AgentInfo:
        """
        Get basic information about the agent.

        Returns:
            AgentInfo: The agent's address, endpoints, protocols, and metadata.
        """
        return AgentInfo(
            agent_address=self.address,
            endpoints=self._endpoints,
            protocols=list(self.protocols.keys()),
            metadata=self.metadata,
        )

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get the metadata associated with the agent.

        Returns:
            Dict[str, Any]: The metadata associated with the agent.
        """
        return self._metadata

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

    def sign_registration(
        self, timestamp: int, sender_wallet_address: Optional[str] = None
    ) -> str:
        """
        Sign the registration data for Almanac contract.

        Args:
            timestamp (int): The timestamp for the registration.
            sender_wallet_address (Optional[str]): The wallet address of the transaction sender.

        Returns:
            str: The signature of the registration data.

        Raises:
            AssertionError: If the Almanac contract is None.
        """
        sender_address = sender_wallet_address or str(self.wallet.address())

        assert self._almanac_contract is not None

        return self._identity.sign_registration(
            str(self._almanac_contract.address),
            timestamp,
            sender_address,
        )

    def update_endpoints(self, endpoints: List[AgentEndpoint]):
        """
        Update the list of endpoints.

        Args:
            endpoints (List[AgentEndpoint]): List of endpoint dictionaries.

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

    def update_registration_policy(self, policy: AgentRegistrationPolicy):
        """
        Update the registration policy.

        Args:
            policy: The registration policy.

        """

        self._registration_policy = policy

    async def register(self):
        """
        Register with the Almanac contract.

        This method checks for registration conditions and performs registration
        if necessary.

        """
        assert self._registration_policy is not None, "Agent has no registration policy"

        await self._registration_policy.register(
            self.address, list(self.protocols.keys()), self._endpoints, self._metadata
        )

    async def _schedule_registration(self):
        """
        Execute the registration loop.

        This method registers with the Almanac contract and schedules the next
        registration.

        """
        while True:
            time_until_next_registration = REGISTRATION_UPDATE_INTERVAL_SECONDS
            try:
                await self.register()
            except InsufficientFundsError:
                time_until_next_registration = 2 * AVERAGE_BLOCK_INTERVAL
            except Exception as ex:
                self._logger.exception(f"Failed to register: {ex}")
                time_until_next_registration = REGISTRATION_RETRY_INTERVAL_SECONDS

            await asyncio.sleep(time_until_next_registration)

    def on_interval(
        self,
        period: float,
        messages: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
    ):
        """
        Decorator to register an interval handler for the provided period.

        Args:
            period (float): The interval period.
            messages (Optional[Union[Type[Model], Set[Type[Model]]]]): Optional message types.

        Returns:
            Callable: The decorator function for registering interval handlers.

        """

        return self._protocol.on_interval(period, messages)

    def on_query(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
    ):
        """
        Set up a query event with a callback.

        Args:
            model (Type[Model]): The query model.
            replies (Optional[Union[Model, Set[Model]]]): Optional reply models.

        Returns:
            Callable: The decorator function for registering query handlers.

        """

        return self._protocol.on_query(model, replies)

    def on_message(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        allow_unverified: Optional[bool] = False,
    ):
        """
        Decorator to register an message handler for the provided message model.

        Args:
            model (Type[Model]): The message model.
            replies (Optional[Union[Type[Model], Set[Type[Model]]]]): Optional reply models.
            allow_unverified (Optional[bool]): Allow unverified messages.

        Returns:
            Callable: The decorator function for registering message handlers.

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

    def _on_rest(
        self,
        method: RestMethod,
        endpoint: str,
        request: Optional[Type[Model]],
        response: Type[Model],
    ):
        if self._init_done and self._server.has_rest_endpoint(method, endpoint):
            self._logger.warning(
                f"Discarding duplicate REST endpoint: {method} {endpoint}"
            )
            return lambda func: func

        def decorator_on_rest(func: RestHandler):
            @functools.wraps(RestGetHandler if method == "GET" else RestPostHandler)  # type: ignore
            def handler(*args, **kwargs):
                return func(*args, **kwargs)

            self._rest_handlers[(method, endpoint)] = handler

            self._server.add_rest_endpoint(
                self.address, method, endpoint, request, response
            )

            return handler

        return decorator_on_rest

    def on_rest_get(self, endpoint: str, response: Type[Model]):
        return self._on_rest("GET", endpoint, None, response)

    def on_rest_post(self, endpoint: str, request: Type[Model], response: Type[Model]):
        return self._on_rest("POST", endpoint, request, response)

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

    def on_wallet_message(
        self,
    ):
        """
        Add a handler for wallet messages.

        """
        if self._wallet_messaging_client is None:
            self._logger.warning(
                "Discarding 'on_wallet_message' handler because wallet messaging is disabled"
            )
            return lambda func: func
        return self._wallet_messaging_client.on_message()

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
                self._signed_message_handlers[schema_digest] = (
                    protocol.signed_message_handlers[schema_digest]
                )
            elif schema_digest in protocol.unsigned_message_handlers:
                self._unsigned_message_handlers[schema_digest] = (
                    protocol.unsigned_message_handlers[schema_digest]
                )
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
        Publish a protocol manifest to the Almanac service.

        Args:
            manifest (Dict[str, Any]): The protocol manifest.

        """
        try:
            resp = requests.post(
                f"{self._agentverse.url}/v1/almanac/manifests",
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
        Handle an incoming message.

        Args:
            sender: The sender of the message.
            schema_digest (str): The digest of the message schema.
            message (JsonStr): The message content in JSON format.
            session (uuid.UUID): The session UUID.

        """
        await self._message_queue.put((schema_digest, sender, message, session))

    async def handle_rest(
        self, method: RestMethod, endpoint: str, message: Optional[Model]
    ) -> Optional[Union[Dict[str, Any], Model]]:
        """
        Handle a REST request.

        Args:
            method (RestMethod): The REST method.
            endpoint (str): The REST endpoint.
            message (Model): The message content.

        """
        handler = self._rest_handlers.get((method, endpoint))
        if not handler:
            return None

        args = []
        args.append(self._build_context())
        if message:
            args.append(message)

        return await handler(*args)  # type: ignore

    async def _startup(self):
        """
        Perform startup actions.

        """
        self._logger.info(f"Starting agent with address: {self.address}")
        if self._registration_policy:
            if self._endpoints:
                self.start_registration_loop()
            else:
                self._logger.warning(
                    "No endpoints provided. Skipping registration: Agent won't be reachable."
                )
        for handler in self._on_startup:
            try:
                ctx = self._build_context()
                await handler(ctx)
            except OSError as ex:
                self._logger.exception(f"OS Error in startup handler: {ex}")
            except RuntimeError as ex:
                self._logger.exception(f"Runtime Error in startup handler: {ex}")
            except Exception as ex:
                self._logger.exception(f"Exception in startup handler: {ex}")

    async def _shutdown(self):
        """
        Perform shutdown actions.

        """
        try:
            status = AgentStatusUpdate(agent_address=self.address, is_active=False)
            status.sign(self._identity)
            await update_agent_status(status, self._almanac_api_url)
        except Exception as ex:
            self._logger.exception(f"Failed to update agent registration status: {ex}")

        for handler in self._on_shutdown:
            try:
                ctx = self._build_context()
                await handler(ctx)
            except OSError as ex:
                self._logger.exception(f"OS Error in shutdown handler: {ex}")
            except RuntimeError as ex:
                self._logger.exception(f"Runtime Error in shutdown handler: {ex}")
            except Exception as ex:
                self._logger.exception(f"Exception in shutdown handler: {ex}")

    async def setup(self):
        """
        Include the internal agent protocol, run startup tasks, and start background tasks.
        """
        self.include(self._protocol)
        self.start_message_dispenser()
        await self._startup()
        self.start_message_receivers()
        self.start_interval_tasks()

    def start_registration_loop(self):
        """
        Start the registration loop.

        """
        self._loop.create_task(self._schedule_registration())

    def start_message_dispenser(self):
        """
        Start the message dispenser.

        """
        self._loop.create_task(self._dispenser.run())

    def start_interval_tasks(self):
        """
        Start interval tasks for the agent.

        """
        for func, period in self._interval_handlers:
            self._loop.create_task(
                _run_interval(func, self._logger, self._build_context, period)
            )

    def start_message_receivers(self):
        """
        Start message receiving tasks for the agent.

        """
        # start the background message queue processor
        self._loop.create_task(self._process_message_queue())

        # start the wallet messaging client if enabled
        if self._wallet_messaging_client is not None:
            for task in [
                self._wallet_messaging_client.poll_server(),
                self._wallet_messaging_client.process_message_queue(
                    self._build_context
                ),
            ]:
                self._loop.create_task(task)

    async def start_server(self):
        """
        Start the agent's server.

        """
        if self._enable_agent_inspector:
            inspector_url = f"{self._agentverse.url}/inspect/"
            escaped_uri = requests.utils.quote(f"http://127.0.0.1:{self._port}")
            self._logger.info(
                f"Agent inspector available at {inspector_url}"
                f"?uri={escaped_uri}&address={self.address}"
            )
        await self._server.serve()

    async def run_async(self):
        """
        Create all tasks for the agent.

        """
        await self.setup()

        tasks = [self.start_server()]

        # remove server task if mailbox is enabled and no REST handlers are defined
        if self._use_mailbox and not self._rest_handlers:
            _ = tasks.pop()
        if self._use_mailbox and self._mailbox_client is not None:
            tasks.append(self._mailbox_client.run())

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        finally:
            await self._shutdown()
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            _ = [task.cancel() for task in tasks]
            await asyncio.gather(*tasks)

    def run(self):
        """
        Run the agent by itself.
        A fresh event loop is created for the agent and it is closed after the agent stops.

        """
        with contextlib.suppress(asyncio.CancelledError, KeyboardInterrupt):
            self._loop.run_until_complete(self.run_async())
        self._loop.stop()
        self._loop.close()

    def get_message_protocol(
        self, message_schema_digest
    ) -> Optional[Tuple[str, Protocol]]:
        """
        Get the protocol for a given message schema digest.

        """
        for protocol_digest, protocol in self.protocols.items():
            if message_schema_digest in protocol.models:
                return (protocol_digest, protocol)
        return None

    async def _process_message_queue(self):
        """
        Process the message queue.

        """
        while True:
            # get an element from the queue
            schema_digest, sender, message, session = await self._message_queue.get()

            # lookup the model definition
            model_class: Optional[Type[Model]] = self._models.get(schema_digest)
            if model_class is None:
                self._logger.warning(
                    f"Received message with unrecognized schema digest: {schema_digest}"
                )
                continue

            protocol_info = self.get_message_protocol(schema_digest)
            protocol_digest = protocol_info[0] if protocol_info else None

            self._message_cache.add_entry(
                EnvelopeHistoryEntry(
                    version=1,
                    sender=sender,
                    target=self.address,
                    session=session,
                    schema_digest=schema_digest,
                    protocol_digest=protocol_digest,
                    payload=message,
                )
            )

            context = ExternalContext(
                agent=AgentRepresentation(
                    address=self.address,
                    name=self._name,
                    signing_callback=self._identity.sign_digest,
                ),
                storage=self._storage,
                ledger=self._ledger,
                resolver=self._resolver,
                dispenser=self._dispenser,
                wallet_messaging_client=self._wallet_messaging_client,
                logger=self._logger,
                queries=self._queries,
                session=session,
                replies=self._replies,
                message_received=MsgDigest(
                    message=message, schema_digest=schema_digest
                ),
                protocol=protocol_info,
            )

            # sanity check
            assert (
                context.session == session
            ), "Context object should always have message session"

            # parse the received message
            try:
                recovered = model_class.parse_raw(message)
            except ValidationError as ex:
                self._logger.warning(f"Unable to parse message: {ex}")
                await _send_error_message(
                    context,
                    sender,
                    ErrorMessage(
                        error=f"Message does not conform to expected schema: {ex}"
                    ),
                )
                continue

            # attempt to find the handler
            handler: Optional[MessageCallback] = self._unsigned_message_handlers.get(
                schema_digest
            )
            if handler is None:
                if not is_user_address(sender):
                    handler = self._signed_message_handlers.get(schema_digest)
                elif schema_digest in self._signed_message_handlers:
                    await _send_error_message(
                        context,
                        sender,
                        ErrorMessage(
                            error="Message must be sent from verified agent address"
                        ),
                    )
                    continue

            if handler is not None:
                try:
                    await handler(context, sender, recovered)
                except OSError as ex:
                    self._logger.exception(f"OS Error in message handler: {ex}")
                except RuntimeError as ex:
                    self._logger.exception(f"Runtime Error in message handler: {ex}")
                except Exception as ex:
                    self._logger.exception(f"Exception in message handler: {ex}")


class Bureau:
    # pylint: disable=protected-access
    """
    A class representing a Bureau of agents.

    This class manages a collection of agents and orchestrates their execution.

    Attributes:
        _loop (asyncio.AbstractEventLoop): The event loop.
        _agents (List[Agent]): The list of agents to be managed by the bureau.
        _endpoints (List[Dict[str, Any]]): The endpoint configuration for the bureau.
        _port (int): The port on which the bureau's server runs.
        _queries (Dict[str, asyncio.Future]): Dictionary mapping query senders to their
        response Futures.
        _logger (Logger): The logger instance.
        _server (ASGIServer): The ASGI server instance for handling requests.
        _agentverse (AgentverseConfig): The agentverse configuration for the bureau.
        _use_mailbox (bool): A flag indicating whether mailbox functionality is enabled for any
        of the agents.
        _registration_policy (AgentRegistrationPolicy): The registration policy for the bureau.

    """

    def __init__(
        self,
        agents: Optional[List[Agent]] = None,
        port: Optional[int] = None,
        endpoint: Optional[Union[str, List[str], Dict[str, dict]]] = None,
        agentverse: Optional[Union[str, Dict[str, str]]] = None,
        registration_policy: Optional[BatchRegistrationPolicy] = None,
        ledger: Optional[LedgerClient] = None,
        wallet: Optional[LocalWallet] = None,
        seed: Optional[str] = None,
        test: bool = True,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        log_level: Union[int, str] = logging.INFO,
    ):
        """
        Initialize a Bureau instance.

        Args:
            agents (Optional[List[Agent]]): The list of agents to be managed by the bureau.
            port (Optional[int]): The port number for the server.
            endpoint (Optional[Union[str, List[str], Dict[str, dict]]]): The endpoint configuration.
            agentverse (Optional[Union[str, Dict[str, str]]]): The agentverse configuration.
            registration_policy (Optional[BatchRegistrationPolicy]): The registration policy.
            ledger (Optional[LedgerClient]): The ledger for the bureau.
            wallet (Optional[LocalWallet]): The wallet for the bureau (overrides 'seed').
            seed (Optional[str]): The seed phrase for the wallet (overridden by 'wallet').
            test (Optional[bool]): True if the bureau will register and transact on the testnet.
            loop (Optional[asyncio.AbstractEventLoop]): The event loop.
            log_level (Union[int, str]): The logging level for the bureau.
        """
        self._loop = loop or asyncio.get_event_loop_policy().get_event_loop()
        self._agents: List[Agent] = []
        self._port = port or 8000
        self._queries: Dict[str, asyncio.Future] = {}
        self._logger = get_logger("bureau", log_level)
        self._server = ASGIServer(
            port=self._port,
            loop=self._loop,
            queries=self._queries,
            logger=self._logger,
        )
        self._agentverse = parse_agentverse_config(agentverse)
        self._endpoints = parse_endpoint_config(
            endpoint, self._agentverse, False, False, self._logger
        )
        self._use_mailbox = any(
            [
                is_mailbox_agent(agent._endpoints, self._agentverse)
                for agent in self._agents
            ]
        )
        almanac_contract = get_almanac_contract(test)

        if wallet and seed:
            self._logger.warning(
                "Ignoring 'seed' argument because 'wallet' is provided."
            )
        elif seed:
            wallet = LocalWallet(
                PrivateKey(derive_key_from_seed(seed, LEDGER_PREFIX, 0)),
                prefix=LEDGER_PREFIX,
            )

        if registration_policy is not None:
            if (
                isinstance(registration_policy, BatchLedgerRegistrationPolicy)
                and wallet is None
            ):
                raise ValueError(
                    "Argument 'wallet' must be provided when using "
                    "the batch ledger registration policy."
                )
            self._registration_policy = registration_policy
        else:
            self._registration_policy = DefaultBatchRegistrationPolicy(
                ledger or get_ledger(test),
                wallet,
                almanac_contract,
                test,
                logger=self._logger,
                almanac_api=f"{self._agentverse.url}/v1/almanac",
            )

        if agents is not None:
            for agent in agents:
                self.add(agent)

    def _update_agent(self, agent: Agent):
        """
        Update the agent to be taken over by the Bureau.

        Args:
            agent (Agent): The agent to be updated.

        """
        agent.update_loop(self._loop)
        agent.update_queries(self._queries)
        if is_mailbox_agent(agent._endpoints, self._agentverse):
            self._use_mailbox = True
        else:
            if agent._endpoints:
                self._logger.warning(
                    f"Overwriting the agent's endpoints {agent._endpoints} "
                    f"with the Bureau's endpoints {self._endpoints}."
                )
            agent.update_endpoints(self._endpoints)
        self._server._rest_handler_map.update(agent._server._rest_handler_map)

        # Run the batch Almanac API registration by default and only run the agent's
        # ledger registration if the Bureau is not using a batch ledger registration
        # policy because it has no wallet address.
        agent._registration_policy = None
        if (
            isinstance(self._registration_policy, DefaultBatchRegistrationPolicy)
            and self._registration_policy._ledger_policy is None
            and agent._almanac_contract is not None
        ):
            agent._registration_policy = LedgerBasedRegistrationPolicy(
                agent._identity,
                agent._ledger,
                agent._wallet,
                agent._almanac_contract,
                agent._test,
                logger=agent._logger,
            )

        agent._agentverse = self._agentverse
        agent._logger.setLevel(self._logger.level)

    def add(self, agent: Agent):
        """
        Add an agent to the bureau.

        Args:
            agent (Agent): The agent to be added.

        """
        if agent in self._agents:
            return
        self._update_agent(agent)
        self._registration_policy.add_agent(agent.info, agent._identity)
        self._agents.append(agent)

    async def _schedule_registration(self):
        """
        Start the batch registration loop.

        """
        if not any(agent._endpoints for agent in self._agents):
            return

        while True:
            time_to_next_registration = REGISTRATION_UPDATE_INTERVAL_SECONDS
            try:
                await self._registration_policy.register()
            except InsufficientFundsError:
                time_to_next_registration = 2 * AVERAGE_BLOCK_INTERVAL
            except Exception as ex:
                self._logger.exception(f"Failed to register: {ex}")
                time_to_next_registration = REGISTRATION_RETRY_INTERVAL_SECONDS

            await asyncio.sleep(time_to_next_registration)

    async def run_async(self):
        """
        Run the agents managed by the bureau.

        """
        tasks = [self._server.serve()]
        if not self._agents:
            self._logger.warning("No agents to run.")
            return
        for agent in self._agents:
            await agent.setup()
            if (
                is_mailbox_agent(agent._endpoints, self._agentverse)
                and agent.mailbox_client is not None
            ):
                tasks.append(agent.mailbox_client.run())
        self._loop.create_task(self._schedule_registration())

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        finally:
            for agent in self._agents:
                await agent._shutdown()
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            _ = [task.cancel() for task in tasks]
            await asyncio.gather(*tasks)

    def run(self):
        """
        Run the bureau.

        """
        with contextlib.suppress(asyncio.CancelledError, KeyboardInterrupt):
            self._loop.run_until_complete(self.run_async())
        self._loop.stop()
        self._loop.close()
