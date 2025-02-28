

# src.uagents.agent

Agent



## AgentRepresentation Objects

```python
class AgentRepresentation()
```

Represents an agent in the context of a message.

**Attributes**:

- `_address` _str_ - The address of the agent.
- `_name` _Optional[str]_ - The name of the agent.
- `_signing_callback` _Callable_ - The callback for signing messages.
  
  Properties:
- `name` _str_ - The name of the agent.
- `address` _str_ - The address of the agent.
- `identifier` _str_ - The agent's address and network prefix.
  

**Methods**:

- `sign_digest(data` - bytes) -> str: Sign the provided data with the agent's identity.



#### __init__
```python
def __init__(address: str, name: Optional[str], signing_callback: Callable)
```

Initialize the AgentRepresentation instance.

**Arguments**:

- `address` _str_ - The address of the context.
- `name` _Optional[str]_ - The optional name associated with the context.
- `signing_callback` _Callable_ - The callback for signing messages.



#### name
```python
@property
def name() -> str
```

Get the name associated with the context or a truncated address if name is None.

**Returns**:

- `str` - The name or truncated address.



#### address
```python
@property
def address() -> str
```

Get the address of the context.

**Returns**:

- `str` - The address of the context.



#### identifier
```python
@property
def identifier() -> str
```

Get the address of the agent used for communication including the network prefix.

**Returns**:

- `str` - The agent's address and network prefix.



#### sign_digest
```python
def sign_digest(data: bytes) -> str
```

Sign the provided data with the callback of the agent's identity.

**Arguments**:

- `data` _bytes_ - The data to sign.
  

**Returns**:

- `str` - The signature of the data.



## Agent Objects

```python
class Agent(Sink)
```

An agent that interacts within a communication environment.

**Attributes**:

- `_name` _str_ - The name of the agent.
- `_port` _int_ - The port on which the agent's server runs.
- `_background_tasks` _Set[asyncio.Task]_ - Set of background tasks associated with the agent.
- `_resolver` _Resolver_ - The resolver for agent communication.
- `_loop` _asyncio.AbstractEventLoop_ - The asyncio event loop used by the agent.
- `_logger` - The logger instance for logging agent activities.
- `_endpoints` _List[AgentEndpoint]_ - List of endpoin[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/agent.py#L38)
ts at which the agent is reachable.
- `_use_mailbox` _bool_ - Indicates if the agent uses a mailbox for communication.
- `_agentverse` _AgentverseConfig_ - Agentverse configuration settings.
- `_mailbox_client` _MailboxClient_ - The client for interacting with the agentverse mailbox.
- `_ledger` - The client for interacting with the blockchain ledger.
- `_almanac_contract` - The almanac contract for registering agent addresses to endpoints.
- `_storage` - Key-value store for agent data storage.
- `_interval_handlers` _List[Tuple[IntervalCallback, float]]_ - List of interval
  handlers and their periods.
- `_interval_messages` _Set[str]_ - Set of message digests that may be sent by interval tasks.
- `_signed_message_handlers` _Dict[str, MessageCallback]_ - Handlers for signed messages.
- `_unsigned_message_handlers` _Dict[str, MessageCallback]_ - Handlers for
  unsigned messages.
- `_message_cache` _EnvelopeHistory_ - History of messages received by the agent.
- `_models` _Dict[str, Type[Model]]_ - Dictionary mapping supported message digests to messages.
- `_replies` _Dict[str, Dict[str, Type[Model]]]_ - Dictionary of allowed replies for each type
  of incoming message.
- `_queries` _Dict[str, asyncio.Future]_ - Dictionary mapping query senders to their response
  Futures.
- `_dispatcher` - The dispatcher for internal handling/sorting of messages.
- `_dispenser` - The dispatcher for external message handling.
- `_message_queue` - Asynchronous queue for incoming messages.
- `_on_startup` _List[Callable]_ - List of functions to run on agent startup.
- `_on_shutdown` _List[Callable]_ - List of functions to run on agent shutdown.
- `_version` _str_ - The version of the agent.
- `_protocol` _Protocol_ - The internal agent protocol consisting of all interval and message
  handlers assigned with agent decorators.
- `protocols` _Dict[str, Protocol]_ - Dictionary mapping all supported protocol digests to their
  corresponding protocols.
- `_ctx` _Context_ - The context for agent interactions.
- `_network` _str_ - The network to use for the agent ('mainnet' or 'testnet').
- `_prefix` _str_ - The address prefix for the agent (determined by the network).
- `_enable_agent_inspector` _bool_ - Enable the agent inspector REST endpoints.
- `_metadata` _Dict[str, Any]_ - Metadata associated with the agent.
- `_readme` _Optional[str]_ - The agent's README file.
- `_avatar_url` _Optional[str]_ - The URL for the agent's avatar image on Agentverse.
  
  Properties:
- `name` _str_ - The name of the agent.
- `address` _str_ - The address of the agent used for communication.
- `identifier` _str_ - The Agent Identifier, including network prefix and address.
- `wallet` _LocalWallet_ - The agent's wallet for transacting on the ledger.
- `storage` _KeyValueStore_ - The key-value store for storage operations.
- `agentverse` _AgentverseConfig_ - The agentverse configuration for the agent.
- `mailbox_client` _MailboxClient_ - The client for interacting with the agentverse mailbox.
- `protocols` _Dict[str, Protocol]_ - Dictionary mapping all supported protocol digests to their
  corresponding protocols.
- `metadata` _Optional[Dict[str, Any]]_ - Metadata associated with the agent.



#### __init__
```python[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/agent.py#L183)
def __init__(name: Optional[str] = None,
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
             network: AgentNetwork = "testnet",
             loop: Optional[asyncio.AbstractEventLoop] = None,
             log_level: Union[int, str] = logging.INFO,
             enable_agent_inspector: bool = True,
             metadata: Optional[Dict[str, Any]] = None,
             readme_path: Optional[str] = None,
             avatar_url: Optional[str] = None,
             publish_agent_details: bool = False)
```

Initialize an Agent instance.

**Arguments**:

- `name` _Optional[str]_ - The name of the agent.
- `port` _Optional[int]_ - The port on which the agent's server will run.
- `seed` _Optional[str]_ - The seed for generating keys.
- `endpoint` _Optional[Union[str, List[str], Dict[str, dict]]]_ - The endpoint configuration.
- `agentverse` _Optional[Union[str, Dict[str, str]]]_ - The agentverse configuration.
- `mailbox` _bool_ - True if the agent will receive messages via an Agentverse mailbox.
- `proxy` _bool_ - True if the agent will receive messages via an Agentverse proxy endpoint.
- `resolve` _Optional[Resolver]_ - The resolver to use for agent communication.
- `enable_wallet_messaging` _Optional[Union[bool, Dict[str, str]]]_ - Whether to enable
  wallet messaging. If '{"chain_id": CHAIN_ID}' is provided, this sets the chain ID for
  the messaging server.
- `wallet_key_derivation_index` _Optional[int]_ - The index used for deriving the wallet key.
- `max_resolver_endpoints` _Optional[int]_ - The maximum number of endpoints to resolve.
- `version` _Optional[str]_ - The version of the agent.
- `network` _Literal["mainnet", "testnet"]_ - The network to use for the agent.
- `loop` _Optional[asyncio.AbstractEventLoop]_ - The asyncio event loop to use.
- `log_level` _Union[int, str]_ - The logging level for the agent.
- `enable_agent_inspector` _bool_ - Enable the agent inspector for debugging.
- `metadata` _Optional[Dict[str, Any]]_ - Optional metadata to include in the agent object.
- `readme_path` _Optional[str]_ - The path to the agent's README file.
- `avatar_url` _Optional[str]_ - The URL for the agent's avatar image on Agentverse.
- `publish_agent_details` _bool_ - Publish agent details to Agentverse on connection via
  local agent inspector.



#### initialize_wallet_messaging
```python
def initialize_wallet_messaging(enable_wallet_messaging: Union[bool,
                                                               Dict[str,
                                                                    str]])
```

Initialize wallet messaging for the agent.

**Arguments**:

- `enable_wallet_messaging` _Union[bool, Dict[str, str]]_ - Wallet messaging configuration.



#### name
```python
@property
def name() -> str
```

Get the name of the agent.

**Returns**:

- `str` - The name of the agent.



#### address
```python
@property
def address() -> str
```

Get the address of the agent used for communication.

**Returns**:

- `str` - The agent's address.



#### identifier
```python
@property
def identifier() -> str
```

Get the Agent Identifier, including network prefix and address.

**Returns**:

- `str` - The agent's identifier.



#### wallet
```python
@property
def wallet() -> LocalWallet
```

Get the wallet of the agent.

**Returns**:

- `LocalWallet` - The agent's wallet.



#### ledger
```python
@property
def ledger() -> LedgerClient
```

Get the ledger of the agent.

**Returns**:

- `LedgerClient` - The agent's ledger



#### storage
```python
@property
def storage() -> KeyValueStore
```

Get the key-value store used by the agent for data storage.

**Returns**:

- `KeyValueStore` - The key-value store instance.



#### agentverse
```python
@property
def agentverse() -> AgentverseConfig
```

Get the agentverse configuration of the agent.

**Returns**:

  Dict[str, str]: The agentverse configuration.



#### mailbox_client
```python
@property
def mailbox_client() -> Optional[MailboxClient]
```

Get the mailbox client used by the agent for mailbox communication.

**Returns**:

- `Optional[MailboxClient]` - The mailbox client instance.



#### balance
```python
@property
def balance() -> int
```

Get the balance of the agent.

**Returns**:

- `int` - Bank balance.



#### info
```python
@property
def info() -> AgentInfo
```

Get basic information about the agent.

**Returns**:

- `AgentInfo` - The agent's address, endpoints, protocols, and metadata.



#### metadata
```python
@property
def metadata() -> Dict[str, Any]
```

Get the metadata associated with the agent.

**Returns**:

  Dict[str, Any]: The metadata associated with the agent.



#### agentverse

```python
@agentverse.setter
def agentverse(config: Union[str, Dict[str, str]])
```

Set the agentverse configuration for the agent.

**Arguments**:

- `config` _Union[str, Dict[str, str]]_ - The new agentverse configuration.



#### sign
```python
def sign(data: bytes) -> str
```

Sign the provided data.

**Arguments**:

- `data` _bytes_ - The data to be signed.
  

**Returns**:

- `str` - The signature of the data.



#### sign_digest
```python
def sign_digest(digest: bytes) -> str
```

Sign the provided digest.

**Arguments**:

- `digest` _bytes_ - The digest to be signed.
  

**Returns**:

- `str` - The signature of the digest.



#### sign_registration
```python
def sign_registration(timestamp: int,
                      sender_wallet_address: Optional[str] = None) -> str
```

Sign the registration data for Almanac contract.

**Arguments**:

- `timestamp` _int_ - The timestamp for the registration.
- `sender_wallet_address` _Optional[str]_ - The wallet address of the transaction sender.
  

**Returns**:

- `str` - The signature of the registration data.
  

**Raises**:

- `AssertionError` - If the Almanac contract is None.



#### update_endpoints
```python
def update_endpoints(endpoints: List[AgentEndpoint])
```

Update the list of endpoints.

**Arguments**:

- `endpoints` _List[AgentEndpoint]_ - List of endpoint dictionaries.



#### update_loop
```python
def update_loop(loop)
```

Update the event loop.

**Arguments**:

- `loop` - The event loop.



#### update_queries
```python
def update_queries(queries)
```

Update the queries attribute.

**Arguments**:

- `queries` - The queries attribute.



#### update_registration_policy
```python
def update_registration_policy(policy: AgentRegistrationPolicy)
```

Update the registration policy.

**Arguments**:

- `policy` - The registration policy.



#### register
```python
async def register()
```

Register with the Almanac contract.

This method checks for registration conditions and performs registration
if necessary.



#### on_interval
```python
def on_interval(period: float,
                messages: Optional[Union[Type[Model],
                                         Set[Type[Model]]]] = None)
```

Decorator to register an interval handler for the provided period.

**Arguments**:

- `period` _float_ - The interval period.
- `messages` _Optional[Union[Type[Model], Set[Type[Model]]]]_ - Optional message types.
  

**Returns**:

- `Callable` - The decorator function for registering interval handlers.



#### on_query
```python
def on_query(model: Type[Model],
             replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None)
```

Set up a query event with a callback.

**Arguments**:

- `model` _Type[Model]_ - The query model.
- `replies` _Optional[Union[Model, Set[Model]]]_ - Optional reply models.
  

**Returns**:

- `Callable` - The decorator function for registering query handlers.



#### on_message
```python
def on_message(model: Type[Model],
               replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
               allow_unverified: Optional[bool] = False)
```

Decorator to register an message handler for the provided message model.

**Arguments**:

- `model` _Type[Model]_ - The message model.
- `replies` _Optional[Union[Type[Model], Set[Type[Model]]]]_ - Optional reply models.
- `allow_unverified` _Optional[bool]_ - Allow unverified messages.
  

**Returns**:

- `Callable` - The decorator function for registering message handlers.



#### on_event
```python
def on_event(event_type: str)
```

Decorator to register an event handler for a specific event type.

**Arguments**:

- `event_type` _str_ - The type of event.
  

**Returns**:

- `Callable` - The decorator function for registering event handlers.



#### on_rest_get
```python
def on_rest_get(endpoint: str, response: Type[Model])
```

Add a handler for a GET REST endpoint.



#### on_rest_post
```python
def on_rest_post(endpoint: str, request: Type[Model], response: Type[Model])
```

Add a handler for a POST REST endpoint.



#### on_wallet_message
```python
def on_wallet_message()
```

Add a handler for wallet messages.



#### include
```python
def include(protocol: Protocol, publish_manifest: Optional[bool] = False)
```

Include a protocol into the agent's capabilities.

**Arguments**:

- `protocol` _Protocol_ - The protocol to include.
- `publish_manifest` _Optional[bool]_ - Flag to publish the protocol's manifest.
  

**Raises**:

- `RuntimeError` - If a duplicate model, signed message handler, or message handler
  is encountered.



#### publish_manifest
```python
def publish_manifest(manifest: Dict[str, Any])
```

Publish a protocol manifest to the Almanac service.

**Arguments**:

- `manifest` _Dict[str, Any]_ - The protocol manifest.



#### handle_message
```python
async def handle_message(sender, schema_digest: str, message: JsonStr,
                         session: uuid.UUID)
```

Handle an incoming message.

**Arguments**:

- `sender` - The sender of the message.
- `schema_digest` _str_ - The digest of the message schema.
- `message` _JsonStr_ - The message content in JSON format.
- `session` _uuid.UUID_ - The session UUID.



#### handle_rest
```python
async def handle_rest(
        method: RestMethod, endpoint: str,
        message: Optional[Model]) -> Optional[Union[Dict[str, Any], Model]]
```

Handle a REST request.

**Arguments**:

- `method` _RestMethod_ - The REST method.
- `endpoint` _str_ - The REST endpoint.
- `message` _Model_ - The message content.



#### setup
```python
async def setup()
```

Include the internal agent protocol, run startup tasks, and start background tasks.



#### start_registration_loop
```python
def start_registration_loop()
```

Start the registration loop.



#### start_message_dispenser
```python
def start_message_dispenser()
```

Start the message dispenser.



#### start_interval_tasks
```python
def start_interval_tasks()
```

Start interval tasks for the agent.



#### start_message_receivers
```python
def start_message_receivers()
```

Start message receiving tasks for the agent.



#### start_server
```python
async def start_server()
```

Start the agent's server.



#### run_async
```python
async def run_async()
```

Create all tasks for the agent.



#### run
```python
def run()
```

Run the agent by itself.
A fresh event loop is created for the agent and it is closed after the agent stops.



#### get_message_protocol
```python
def get_message_protocol(
        message_schema_digest) -> Optional[Tuple[str, Protocol]]
```

Get the protocol for a given message schema digest.



## Bureau Objects

```python
class Bureau()
```

A class representing a Bureau of agents.

This class manages a collection of agents and orchestrates their execution.

**Attributes**:

- `_loop` _asyncio.AbstractEventLoop_ - The event loop.
- `_agents` _List[Agent]_ - The list of agents to be managed by the bureau.
- `_endpoints` _List[Dict[str, Any]]_ - The endpoint configuration for the bureau.
- `_port` _int_ - The port on which the bureau's server runs.
- `_queries` _Dict[str, asyncio.Future]_ - Dictionary mapping query senders to their
  response Futures.
- `_logger` _Logger_ - The logger instance.
- `_server` _ASGIServer_ - The ASGI server instance for handling requests.
- `_agentverse` _AgentverseConfig_ - The agentverse configuration for the bureau.
- `_use_mailbox` _bool_ - A flag indicating whether mailbox functionality is enabled for any
  of the agents.
- `_registration_policy` _AgentRegistrationPolicy_ - The registration policy for the bureau.



#### __init__
```python
def __init__(agents: Optional[List[Agent]] = None,
             port: Optional[int] = None,
             endpoint: Optional[Union[str, List[str], Dict[str, dict]]] = None,
             agentverse: Optional[Union[str, Dict[str, str]]] = None,
             registration_policy: Optional[BatchRegistrationPolicy] = None,
             ledger: Optional[LedgerClient] = None,
             wallet: Optional[LocalWallet] = None,
             seed: Optional[str] = None,
             network: AgentNetwork = "testnet",
             loop: Optional[asyncio.AbstractEventLoop] = None,
             log_level: Union[int, str] = logging.INFO)
```

Initialize a Bureau instance.

**Arguments**:

- `agents` _Optional[List[Agent]]_ - The list of agents to be managed by the bureau.
- `port` _Optional[int]_ - The port number for the server.
- `endpoint` _Optional[Union[str, List[str], Dict[str, dict]]]_ - The endpoint configuration.
- `agentverse` _Optional[Union[str, Dict[str, str]]]_ - The agentverse configuration.
- `registration_policy` _Optional[BatchRegistrationPolicy]_ - The registration policy.
- `ledger` _Optional[LedgerClient]_ - The ledger for the bureau.
- `wallet` _Optional[LocalWallet]_ - The wallet for the bureau (overrides 'seed').
- `seed` _Optional[str]_ - The seed phrase for the wallet (overridden by 'wallet').
- `network` _Literal["mainnet", "testnet"]_ - The network to use for the agent.
- `loop` _Optional[asyncio.AbstractEventLoop]_ - The event loop.
- `log_level` _Union[int, str]_ - The logging level for the bureau.



#### add
```python
def add(agent: Agent)
```

Add an agent to the bureau.

**Arguments**:

- `agent` _Agent_ - The agent to be added.



#### run_async
```python
async def run_async()
```

Run the agents managed by the bureau.



#### run
```python
def run()
```

Run the bureau.

