<a id="src.uagents.context"></a>

# src.uagents.context

Agent Context and Message Handling

<a id="src.uagents.context.MsgDigest"></a>

## MsgDigest Objects

```python
@dataclass
class MsgDigest()
```

Represents a message digest containing a message and its schema digest.

**Attributes**:

- `message` _Any_ - The message content.
- `schema_digest` _str_ - The schema digest of the message.

<a id="src.uagents.context.Context"></a>

## Context Objects

```python
class Context()
```

Represents the context in which messages are handled and processed.

**Attributes**:

- `storage` _KeyValueStore_ - The key-value store for storage operations.
- `wallet` _LocalWallet_ - The agent's wallet for transacting on the ledger.
- `ledger` _LedgerClient_ - The client for interacting with the blockchain ledger.
- `_name` _Optional[str]_ - The name of the agent.
- `_address` _str_ - The address of the agent.
- `_resolver` _Resolver_ - The resolver for address-to-endpoint resolution.
- `_identity` _Identity_ - The agent's identity.
- `_queries` _Dict[str, asyncio.Future]_ - Dictionary mapping query senders to their
  response Futures.
- `_session` _Optional[uuid.UUID]_ - The session UUID.
- `_replies` _Optional[Dict[str, Set[Type[Model]]]]_ - Dictionary of allowed reply digests
  for each type of incoming message.
- `_interval_messages` _Optional[Set[str]]_ - Set of message digests that may be sent by
  interval tasks.
- `_message_received` _Optional[MsgDigest]_ - The message digest received.
- `_protocols` _Optional[Dict[str, Protocol]]_ - Dictionary mapping all supported protocol
  digests to their corresponding protocols.
- `_logger` _Optional[logging.Logger]_ - The optional logger instance.
  
  Properties:
- `name` _str_ - The name of the agent.
- `address` _str_ - The address of the agent.
- `logger` _logging.Logger_ - The logger instance.
- `protocols` _Optional[Dict[str, Protocol]]_ - Dictionary mapping all supported protocol
  digests to their corresponding protocols.
- `session` _uuid.UUID_ - The session UUID.
  

**Methods**:

- `get_message_protocol(message_schema_digest)` - Get the protocol associated
  with a message schema digest.
  send(destination, message, timeout): Send a message to a destination.
  send_raw(destination, json_message, schema_digest, message_type, timeout): Send a message
  with the provided schema digest to a destination.
  experimental_broadcast(destination_protocol, message, limit, timeout): Broadcast a message
  to agents with a specific protocol.

<a id="src.uagents.context.Context.__init__"></a>

#### `__`init`__`

```python
def __init__(address: str,
             name: Optional[str],
             storage: KeyValueStore,
             resolve: Resolver,
             identity: Identity,
             wallet: LocalWallet,
             ledger: LedgerClient,
             queries: Dict[str, asyncio.Future],
             session: Optional[uuid.UUID] = None,
             replies: Optional[Dict[str, Set[Type[Model]]]] = None,
             interval_messages: Optional[Set[str]] = None,
             message_received: Optional[MsgDigest] = None,
             protocols: Optional[Dict[str, Protocol]] = None,
             logger: Optional[logging.Logger] = None)
```

Initialize the Context instance.

**Arguments**:

- `address` _str_ - The address of the context.
- `name` _Optional[str]_ - The optional name associated with the context.
- `storage` _KeyValueStore_ - The key-value store for storage operations.
- `resolve` _Resolver_ - The resolver for name-to-address resolution.
- `identity` _Identity_ - The identity associated with the context.
- `wallet` _LocalWallet_ - The local wallet instance for managing identities.
- `ledger` _LedgerClient_ - The ledger client for interacting with distributed ledgers.
- `queries` _Dict[str, asyncio.Future]_ - Dictionary mapping query senders to their response
  Futures.
- `session` _Optional[uuid.UUID]_ - The optional session UUID.
- `replies` _Optional[Dict[str, Set[Type[Model]]]]_ - Optional dictionary of reply models.
- `interval_messages` _Optional[Set[str]]_ - The optional set of interval messages.
- `message_received` _Optional[MsgDigest]_ - The optional message digest received.
- `protocols` _Optional[Dict[str, Protocol]]_ - The optional dictionary of protocols.
- `logger` _Optional[logging.Logger]_ - The optional logger instance.

<a id="src.uagents.context.Context.name"></a>

#### name

```python
@property
def name() -> str
```

Get the name associated with the context or a truncated address if name is None.

**Returns**:

- `str` - The name or truncated address.

<a id="src.uagents.context.Context.address"></a>

#### address

```python
@property
def address() -> str
```

Get the address of the context.

**Returns**:

- `str` - The address of the context.

<a id="src.uagents.context.Context.logger"></a>

#### logger

```python
@property
def logger() -> logging.Logger
```

Get the logger instance associated with the context.

**Returns**:

- `logging.Logger` - The logger instance.

<a id="src.uagents.context.Context.protocols"></a>

#### protocols

```python
@property
def protocols() -> Optional[Dict[str, Protocol]]
```

Get the dictionary of protocols associated with the context.

**Returns**:

  Optional[Dict[str, Protocol]]: The dictionary of protocols.

<a id="src.uagents.context.Context.session"></a>

#### session

```python
@property
def session() -> uuid.UUID
```

Get the session UUID associated with the context.

**Returns**:

- `uuid.UUID` - The session UUID.

<a id="src.uagents.context.Context.get_message_protocol"></a>

#### get`_`message`_`protocol

```python
def get_message_protocol(message_schema_digest) -> Optional[str]
```

Get the protocol associated with a given message schema digest.

**Arguments**:

- `message_schema_digest` _str_ - The schema digest of the message.
  

**Returns**:

- `Optional[str]` - The protocol digest associated with the message schema digest,
  or None if not found.

<a id="src.uagents.context.Context.get_agents_by_protocol"></a>

#### get`_`agents`_`by`_`protocol

```python
def get_agents_by_protocol(protocol_digest: str,
                           limit: Optional[int] = None) -> List[str]
```

Retrieve a list of agent addresses using a specific protocol digest.

This method queries the Almanac API to retrieve a list of agent addresses
that are associated with a given protocol digest. The list can be optionally
limited to a specified number of addresses.

**Arguments**:

- `protocol_digest` _str_ - The protocol digest to search for, starting with "proto:".
- `limit` _int, optional_ - The maximum number of agent addresses to return.
  

**Returns**:

- `List[str]` - A list of agent addresses using the specified protocol digest.

<a id="src.uagents.context.Context.send"></a>

#### send

```python
async def send(destination: str,
               message: Model,
               timeout: Optional[int] = DEFAULT_ENVELOPE_TIMEOUT_SECONDS)
```

Send a message to the specified destination.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `timeout` _Optional[int]_ - The optional timeout for sending the message, in seconds.

<a id="src.uagents.context.Context.experimental_broadcast"></a>

#### experimental`_`broadcast

```python
async def experimental_broadcast(
        destination_protocol: str,
        message: Model,
        limit: Optional[int] = DEFAULT_SEARCH_LIMIT,
        timeout: Optional[int] = DEFAULT_ENVELOPE_TIMEOUT_SECONDS)
```

Broadcast a message to agents with a specific protocol.

This asynchronous method broadcasts a given message to agents associated
with a specific protocol. The message is sent to multiple agents concurrently.
The schema digest of the message is used for verification.

**Arguments**:

- `destination_protocol` _str_ - The protocol to filter agents by.
- `message` _Model_ - The message to broadcast.
- `limit` _int, optional_ - The maximum number of agents to send the message to.
- `timeout` _int, optional_ - The timeout for sending each message.
  

**Returns**:

  None

<a id="src.uagents.context.Context.send_raw"></a>

#### send`_`raw

```python
async def send_raw(destination: str,
                   json_message: JsonStr,
                   schema_digest: str,
                   message_type: Optional[Type[Model]] = None,
                   timeout: Optional[int] = DEFAULT_ENVELOPE_TIMEOUT_SECONDS)
```

Send a raw message to the specified destination.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `json_message` _JsonStr_ - The JSON-encoded message to be sent.
- `schema_digest` _str_ - The schema digest of the message.
- `message_type` _Optional[Type[Model]]_ - The optional type of the message being sent.
- `timeout` _Optional[int]_ - The optional timeout for sending the message, in seconds.

