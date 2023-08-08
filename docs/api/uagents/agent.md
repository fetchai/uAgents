<a id="src.uagents.agent"></a>

# src.uagents.agent

Agent Framework

<a id="src.uagents.agent.Agent"></a>

## Agent Objects

```python
class Agent(Sink)
```

An agent that interacts within a communication environment.

**Attributes**:

- `_name` _str_ - The name of the agent.
- `_port` _int_ - The port on which the agent runs.
- `_background_tasks` _Set[asyncio.Task]_ - Set of background tasks associated with the agent.
- `_resolver` _Resolver_ - The resolver for agent communication.
- `_loop` _asyncio.AbstractEventLoop_ - The asyncio event loop used by the agent.
- `_logger` - The logger instance for logging agent activities.
- `_endpoints` _List[dict]_ - List of communication endpoints.
- `_use_mailbox` _bool_ - Indicates if the agent uses a mailbox for communication.
- `_agentverse` _dict_ - Agentverse configuration settings.
- `_mailbox_client` _MailboxClient_ - Client for interacting with the mailbox.
- `_ledger` - The ledger for recording agent transactions.
- `_almanac_contract` - The almanac contract for agent metadata.
- `_storage` - Key-value store for agent data storage.
- `_interval_handlers` _List[Tuple[IntervalCallback, float]]_ - List of interval handlers and their periods.
- `_interval_messages` _Set[str]_ - Set of interval message names.
- `_signed_message_handlers` _Dict[str, MessageCallback]_ - Handlers for signed messages.
- `_unsigned_message_handlers` _Dict[str, MessageCallback]_ - Handlers for unsigned messages.
- `_models` _Dict[str, Type[Model]]_ - Dictionary of supported data models.
- `_replies` _Dict[str, Set[Type[Model]]]_ - Dictionary of reply data models.
- `_queries` _Dict[str, asyncio.Future]_ - Dictionary of active queries.
- `_dispatcher` - The dispatcher for message handling.
- `_message_queue` - Asynchronous queue for incoming messages.
- `_on_startup` _List[Callable]_ - List of functions to run on agent startup.
- `_on_shutdown` _List[Callable]_ - List of functions to run on agent shutdown.
- `_version` _str_ - The version of the agent.
- `_protocol` _Protocol_ - The internal agent protocol.
- `protocols` _Dict[str, Protocol]_ - Dictionary of supported protocols.
- `_ctx` _Context_ - The context for agent interactions.
  

**Methods**:

- `__init__` - Initialize the Agent instance.

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
- `port` _Optional[int]_ - The port on which the agent will run.
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

Get the address of the agent's identity.

**Returns**:

- `str` - The address of the agent's identity.

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

Get the mailbox configuration of the agent.

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

Set the mailbox configuration for the agent.

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

Set up an interval event with a callback.

**Arguments**:

- `period` _float_ - The interval period.
- `messages` _Optional[Union[Type[Model], Set[Type[Model]]]]_ - Optional message types.
  

**Returns**:

- `Callable` - The callback function for the interval event.

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

- `Callable` - The callback function for the query event.

<a id="src.uagents.agent.Agent.on_message"></a>

#### on`_`message

```python
def on_message(model: Type[Model],
               replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
               allow_unverified: Optional[bool] = False)
```

Set up a message event with a callback.

**Arguments**:

- `model` _Type[Model]_ - The message model.
- `replies` _Optional[Union[Type[Model], Set[Type[Model]]]]_ - Optional reply models.
- `allow_unverified` _Optional[bool]_ - Allow unverified messages.
  

**Returns**:

- `Callable` - The callback function for the message event.

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

- `RuntimeError` - If a duplicate model, signed message handler, or message handler is encountered.

<a id="src.uagents.agent.Agent.publish_manifest"></a>

#### publish`_`manifest

```python
def publish_manifest(manifest: Dict[str, Any])
```

Publish a protocol manifest to the Almanac.

**Arguments**:

- `manifest` _Dict[str, Any]_ - The protocol manifest.

<a id="src.uagents.agent.Agent.handle_message"></a>

#### handle`_`message

```python
async def handle_message(sender, schema_digest: str, message: JsonStr,
                         session: uuid.UUID)
```

Handle an incoming message asynchronously.

**Arguments**:

- `sender` - The sender of the message.
- `schema_digest` _str_ - The schema digest of the message.
- `message` _JsonStr_ - The message content in JSON format.
- `session` _uuid.UUID_ - The session UUID.

<a id="src.uagents.agent.Agent.setup"></a>

#### setup

```python
def setup()
```

Set up the agent.

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
- `endpoint` _Optional[Union[str, List[str], Dict[str, dict]]]_ - Configuration for agent endpoints.
  

**Attributes**:

- `_loop` _asyncio.AbstractEventLoop_ - The event loop.
- `_agents` _List[Agent]_ - A list of Agent instances within the bureau.
- `_endpoints` _List[Dict[str, Any]]_ - A list of endpoint dictionaries for the agents.
- `_port` _int_ - The port number for the server.
- `_queries` _Dict[str, asyncio.Future]_ - A dictionary of query identifiers to asyncio futures.
- `_logger` _Logger_ - The logger instance.
- `_server` _ASGIServer_ - The ASGI server instance for handling requests.
- `_use_mailbox` _bool_ - A flag indicating whether mailbox functionality is enabled.

<a id="src.uagents.agent.Bureau.add"></a>

#### add

```python
def add(agent: Agent)
```

Add an agent to the bureau.

**Arguments**:

- `agent` _Agent_ - The agent instance to be added.

<a id="src.uagents.agent.Bureau.run"></a>

#### run

```python
def run()
```

Run the agents managed by the bureau.

