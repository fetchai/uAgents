<a id="src.uagents.agent"></a>

# src.uagents.agent

Agent

<a id="src.uagents.agent.Agent"></a>

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
- `_endpoints` _List[dict]_ - List of endpoints at which the agent is reachable.
- `_use_mailbox` _bool_ - Indicates if the agent uses a mailbox for communication.
- `_agentverse` _dict_ - Agentverse configuration settings.
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
- `_models` _Dict[str, Type[Model]]_ - Dictionary mapping supported message digests to messages.
- `_replies` _Dict[str, Set[Type[Model]]]_ - Dictionary of allowed reply digests for each type
  of incoming message.
- `_queries` _Dict[str, asyncio.Future]_ - Dictionary mapping query senders to their response
  Futures.
- `_dispatcher` - The dispatcher for message handling.
- `_message_queue` - Asynchronous queue for incoming messages.
- `_on_startup` _List[Callable]_ - List of functions to run on agent startup.
- `_on_shutdown` _List[Callable]_ - List of functions to run on agent shutdown.
- `_version` _str_ - The version of the agent.
- `_protocol` _Protocol_ - The internal agent protocol consisting of all interval and message
  handlers assigned with agent decorators.
- `protocols` _Dict[str, Protocol]_ - Dictionary mapping all supported protocol digests to their
  corresponding protocols.
- `_ctx` _Context_ - The context for agent interactions.
  
  Properties:
- `name` _str_ - The name of the agent.
- `address` _str_ - The address of the agent used for communication.
- `wallet` _LocalWallet_ - The agent's wallet for transacting on the ledger.
- `storage` _KeyValueStore_ - The key-value store for storage operations.
- `mailbox` _Dict[str, str]_ - The mailbox configuration for the agent (deprecated and replaced
  by agentverse).
- `agentverse` _Dict[str, str]_ - The agentverse configuration for the agent.
- `mailbox_client` _MailboxClient_ - The client for interacting with the agentverse mailbox.
- `protocols` _Dict[str, Protocol]_ - Dictionary mapping all supported protocol digests to their
  corresponding protocols.

<a id="src.uagents.agent.Agent.__init__"></a>

#### `__`init`__`

```python
def __init__(name: Optional[str] = None,
             port: Optional[int] = None,
             seed: Optional[str] = None,
             endpoint: Optional[Union[str, List[str], Dict[str, dict]]] = None,
             agentverse: Optional[Union[str, Dict[str, str]]] = None,
             mailbox: Optional[Union[str, Dict[str, str]]] = None,
             resolve: Optional[Resolver] = None,
             version: Optional[str] = None)
```

Initialize an Agent instance.

**Arguments**:

- `name` _Optional[str]_ - The name of the agent.
- `port` _Optional[int]_ - The port on which the agent's server will run.
- `seed` _Optional[str]_ - The seed for generating keys.
- `endpoint` _Optional[Union[str, List[str], Dict[str, dict]]]_ - The endpoint configuration.
- `agentverse` _Optional[Union[str, Dict[str, str]]]_ - The agentverse configuration.
- `mailbox` _Optional[Union[str, Dict[str, str]]]_ - The mailbox configuration.
- `resolve` _Optional[Resolver]_ - The resolver to use for agent communication.
- `version` _Optional[str]_ - The version of the agent.

<a id="src.uagents.agent.Agent.name"></a>

#### name

```python
@property
def name() -> str
```

Get the name of the agent.

**Returns**:

- `str` - The name of the agent.

<a id="src.uagents.agent.Agent.address"></a>

#### address

```python
@property
def address() -> str
```

Get the address of the agent used for communication.

**Returns**:

- `str` - The agent's address.

<a id="src.uagents.agent.Agent.wallet"></a>

#### wallet

```python
@property
def wallet() -> LocalWallet
```

Get the wallet of the agent.

**Returns**:

- `LocalWallet` - The agent's wallet.

<a id="src.uagents.agent.Agent.storage"></a>

#### storage

```python
@property
def storage() -> KeyValueStore
```

Get the key-value store used by the agent for data storage.

**Returns**:

- `KeyValueStore` - The key-value store instance.

<a id="src.uagents.agent.Agent.mailbox"></a>

#### mailbox

```python
@property
def mailbox() -> Dict[str, str]
```

Get the mailbox configuration of the agent (deprecated and replaced by agentverse).

**Returns**:

  Dict[str, str]: The mailbox configuration.

<a id="src.uagents.agent.Agent.agentverse"></a>

#### agentverse

```python
@property
def agentverse() -> Dict[str, str]
```

Get the agentverse configuration of the agent.

**Returns**:

  Dict[str, str]: The agentverse configuration.

<a id="src.uagents.agent.Agent.mailbox_client"></a>

#### mailbox`_`client

```python
@property
def mailbox_client() -> MailboxClient
```

Get the mailbox client used by the agent for mailbox communication.

**Returns**:

- `MailboxClient` - The mailbox client instance.

<a id="src.uagents.agent.Agent.mailbox"></a>

#### mailbox

```python
@mailbox.setter
def mailbox(config: Union[str, Dict[str, str]])
```

Set the mailbox configuration for the agent (deprecated and replaced by agentverse).

**Arguments**:

- `config` _Union[str, Dict[str, str]]_ - The new mailbox configuration.

<a id="src.uagents.agent.Agent.agentverse"></a>

#### agentverse

```python
@agentverse.setter
def agentverse(config: Union[str, Dict[str, str]])
```

Set the agentverse configuration for the agent.

**Arguments**:

- `config` _Union[str, Dict[str, str]]_ - The new agentverse configuration.

<a id="src.uagents.agent.Agent.sign"></a>

#### sign

```python
def sign(data: bytes) -> str
```

Sign the provided data.

**Arguments**:

- `data` _bytes_ - The data to be signed.
  

**Returns**:

- `str` - The signature of the data.

<a id="src.uagents.agent.Agent.sign_digest"></a>

#### sign`_`digest

```python
def sign_digest(digest: bytes) -> str
```

Sign the provided digest.

**Arguments**:

- `digest` _bytes_ - The digest to be signed.
  

**Returns**:

- `str` - The signature of the digest.

<a id="src.uagents.agent.Agent.sign_registration"></a>

#### sign`_`registration

```python
def sign_registration() -> str
```

Sign the registration data for Almanac contract.

**Returns**:

- `str` - The signature of the registration data.
  

**Raises**:

- `AssertionError` - If the Almanac contract address is None.

<a id="src.uagents.agent.Agent.update_endpoints"></a>

#### update`_`endpoints

```python
def update_endpoints(endpoints: List[Dict[str, Any]])
```

Update the list of endpoints.

**Arguments**:

- `endpoints` _List[Dict[str, Any]]_ - List of endpoint dictionaries.

<a id="src.uagents.agent.Agent.update_loop"></a>

#### update`_`loop

```python
def update_loop(loop)
```

Update the event loop.

**Arguments**:

- `loop` - The event loop.

<a id="src.uagents.agent.Agent.update_queries"></a>

#### update`_`queries

```python
def update_queries(queries)
```

Update the queries attribute.

**Arguments**:

- `queries` - The queries attribute.

<a id="src.uagents.agent.Agent.register"></a>

#### register

```python
async def register()
```

Register with the Almanac contract.

This method checks for registration conditions and performs registration
if necessary.

<a id="src.uagents.agent.Agent.on_interval"></a>

#### on`_`interval

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

<a id="src.uagents.agent.Agent.on_query"></a>

#### on`_`query

```python
def on_query(model: Type[Model],
             replies: Optional[Union[Model, Set[Model]]] = None)
```

Set up a query event with a callback.

**Arguments**:

- `model` _Type[Model]_ - The query model.
- `replies` _Optional[Union[Model, Set[Model]]]_ - Optional reply models.
  

**Returns**:

- `Callable` - The decorator function for registering query handlers.

<a id="src.uagents.agent.Agent.on_message"></a>

#### on`_`message

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

<a id="src.uagents.agent.Agent.on_event"></a>

#### on`_`event

```python
def on_event(event_type: str)
```

Decorator to register an event handler for a specific event type.

**Arguments**:

- `event_type` _str_ - The type of event.
  

**Returns**:

- `Callable` - The decorator function for registering event handlers.

<a id="src.uagents.agent.Agent.include"></a>

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

<a id="src.uagents.agent.Agent.publish_manifest"></a>

#### publish`_`manifest

```python
def publish_manifest(manifest: Dict[str, Any])
```

Publish a protocol manifest to the Almanac service.

**Arguments**:

- `manifest` _Dict[str, Any]_ - The protocol manifest.

<a id="src.uagents.agent.Agent.handle_message"></a>

#### handle`_`message

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

<a id="src.uagents.agent.Agent.setup"></a>

#### setup

```python
def setup()
```

Include the internal agent protocol, run startup tasks, and start background tasks.

<a id="src.uagents.agent.Agent.start_background_tasks"></a>

#### start`_`background`_`tasks

```python
def start_background_tasks()
```

Start background tasks for the agent.

<a id="src.uagents.agent.Agent.run"></a>

#### run

```python
def run()
```

Run the agent.

<a id="src.uagents.agent.Bureau"></a>

## Bureau Objects

```python
class Bureau()
```

A class representing a Bureau of agents.

This class manages a collection of agents and orchestrates their execution.

**Arguments**:

- `port` _Optional[int]_ - The port number for the server.
- `endpoint` _Optional[Union[str, List[str], Dict[str, dict]]]_ - Configuration
  for agent endpoints.
  

**Attributes**:

- `_loop` _asyncio.AbstractEventLoop_ - The event loop.
- `_agents` _List[Agent]_ - The list of agents contained in the bureau.
- `_endpoints` _List[Dict[str, Any]]_ - The endpoint configuration for the bureau.
- `_port` _int_ - The port on which the bureau's server runs.
- `_queries` _Dict[str, asyncio.Future]_ - Dictionary mapping query senders to their
  response Futures.
- `_logger` _Logger_ - The logger instance.
- `_server` _ASGIServer_ - The ASGI server instance for handling requests.
- `_use_mailbox` _bool_ - A flag indicating whether mailbox functionality is enabled for any
  of the agents.

<a id="src.uagents.agent.Bureau.__init__"></a>

#### `__`init`__`

```python
def __init__(port: Optional[int] = None,
             endpoint: Optional[Union[str, List[str], Dict[str,
                                                           dict]]] = None)
```

Initialize a Bureau instance.

**Arguments**:

- `port` _Optional[int]_ - The port on which the bureau's server will run.
- `endpoint` _Optional[Union[str, List[str], Dict[str, dict]]]_ - The endpoint configuration
  for the bureau.

<a id="src.uagents.agent.Bureau.add"></a>

#### add

```python
def add(agent: Agent)
```

Add an agent to the bureau.

**Arguments**:

- `agent` _Agent_ - The agent to be added.

<a id="src.uagents.agent.Bureau.run"></a>

#### run

```python
def run()
```

Run the agents managed by the bureau.

