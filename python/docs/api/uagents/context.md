

# src.uagents.context

Agent Context and Message Handling



## Context Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L53)

```python
class Context(ABC)
```

Represents the context in which messages are handled and processed.

Properties:
agent (AgentRepresentation): The agent representation associated with the context.
storage (KeyValueStore): The key-value store for storage operations.
ledger (LedgerClient): The client for interacting with the blockchain ledger.
logger (logging.Logger): The logger instance.
session (uuid.UUID): The session UUID associated with the context.

**Methods**:

  get_agents_by_protocol(protocol_digest, limit, logger): Retrieve a list of agent addresses
  using a specific protocol digest.
  broadcast(destination_protocol, message, limit, timeout): Broadcast a message
  to agents with a specific protocol.
  send(destination, message, timeout): Send a message to a destination.
  send_raw(destination, json_message, schema_digest, message_type, timeout):
  Send a message with the provided schema digest to a destination.



#### agent[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L75)
```python
@property
@abstractmethod
def agent() -> AgentRepresentation
```

Get the agent representation associated with the context.

**Returns**:

- `AgentRepresentation` - The agent representation.



#### storage[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L86)
```python
@property
@abstractmethod
def storage() -> KeyValueStore
```

Get the key-value store associated with the context.

**Returns**:

- `KeyValueStore` - The key-value store.



#### ledger[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L97)
```python
@property
@abstractmethod
def ledger() -> LedgerClient
```

Get the ledger client associated with the context.

**Returns**:

- `LedgerClient` - The ledger client.



#### logger[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L108)
```python
@property
@abstractmethod
def logger() -> logging.Logger
```

Get the logger instance associated with the context.

**Returns**:

- `logging.Logger` - The logger instance.



#### session[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L119)
```python
@property
@abstractmethod
def session() -> uuid.UUID
```

Get the session UUID associated with the context.

**Returns**:

- `uuid.UUID` - The session UUID.



#### get_agents_by_protocol[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L130)
```python
@abstractmethod
def get_agents_by_protocol(
        protocol_digest: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
        logger: Optional[logging.Logger] = None) -> List[str]
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



#### broadcast[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L152)
```python
@abstractmethod
async def broadcast(
        destination_protocol: str,
        message: Model,
        limit: int = DEFAULT_SEARCH_LIMIT,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS) -> List[MsgStatus]
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

- `List[MsgStatus]` - A list of message delivery statuses.



#### send[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L177)
```python
@abstractmethod
async def send(destination: str,
               message: Model,
               timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS) -> MsgStatus
```

Send a message to the specified destination.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `timeout` _Optional[int]_ - The optional timeout for sending the message, in seconds.
  

**Returns**:

- `MsgStatus` - The delivery status of the message.



#### send_raw[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L197)
```python
@abstractmethod
async def send_raw(
        destination: str,
        message_schema_digest: str,
        message_body: JsonStr,
        sync: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        protocol_digest: Optional[str] = None,
        queries: Optional[Dict[str, asyncio.Future]] = None) -> MsgStatus
```

Send a message to the specified destination where the message body and
message schema digest are sent separately.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message_schema_digest` _str_ - The schema digest of the message to be sent.
- `message_body` _JsonStr_ - The JSON-encoded message body to be sent.
- `sync` _bool_ - Whether to send the message synchronously or asynchronously.
- `timeout` _Optional[int]_ - The optional timeout for sending the message, in seconds.
- `protocol_digest` _Optional[str]_ - The protocol digest of the message to be sent.
- `queries` _Optional[Dict[str, asyncio.Future]]_ - The dictionary of queries to resolve.
  

**Returns**:

- `MsgStatus` - The delivery status of the message.



#### send_and_receive[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L226)
```python
@abstractmethod
async def send_and_receive(
    destination: str,
    message: Model,
    response_type: Type[Model],
    sync: bool = False,
    timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS
) -> Tuple[Optional[Model], MsgStatus]
```

Send a message to the specified destination and receive a response.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `response_type` _Type[Model]_ - The type of the response message.
- `sync` _bool_ - Whether to send the message synchronously or asynchronously.
- `timeout` _int_ - The timeout for sending the message, in seconds.
  

**Returns**:

  Tuple[Optional[Model], MsgStatus]: The response message if received and delivery status



#### send_wallet_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L250)
```python
@abstractmethod
async def send_wallet_message(destination: str, text: str, msg_type: int = 1)
```

Send a message to the wallet of the specified destination.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `text` _str_ - The text of the message to be sent.
- `msg_type` _int_ - The type of the message to be sent.
  

**Returns**:

  None



## InternalContext Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L271)

```python
class InternalContext(Context)
```

Represents the agent internal context for proactive behaviour.



#### session[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L315)
```python
@property
def session() -> uuid.UUID
```

Get the session UUID associated with the context.

**Returns**:

- `uuid.UUID` - The session UUID.



#### outbound_messages[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L325)
```python
@property
def outbound_messages() -> Dict[str, Tuple[JsonStr, str]]
```

Get the dictionary of outbound messages associated with the context.

**Returns**:

  Dict[str, Tuple[JsonStr, str]]: The dictionary of outbound messages.



#### address[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L335)
```python
@property
@deprecated("Please use `ctx.agent.address` instead.")
def address() -> str
```

Get the agent address associated with the context.
This is a deprecated property and will be removed in a future release.
Please use the `ctx.agent.address` property instead.

**Returns**:

- `str` - The agent address.



#### send[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L423)
```python
async def send(destination: str,
               message: Model,
               timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS) -> MsgStatus
```

This is the pro-active send method which is used in on_event and
on_interval methods. In these methods, interval messages are set but
we don't have access properties that are only necessary in re-active
contexts, like 'replies', 'message_received', or 'protocol'.



#### send_and_receive[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L570)
```python
async def send_and_receive(
    destination: str,
    message: Model,
    response_type: Type[Model],
    sync: bool = False,
    timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS
) -> Tuple[Optional[Model], MsgStatus]
```

Send a message to the specified destination and receive a response.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `response_type` _Type[Model]_ - The type of the response message.
- `sync` _bool_ - Whether to send the message synchronously or asynchronously.
- `timeout` _int_ - The timeout for sending the message, in seconds.
  

**Returns**:

  Tuple[Optional[Model], MsgStatus]: The response message if received and delivery status



## ExternalContext Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L653)

```python
class ExternalContext(InternalContext)
```

Represents the reactive context in which messages are handled and processed.

**Attributes**:

- `_queries` _Dict[str, asyncio.Future]_ - Dictionary mapping query senders to their
  response Futures.
- `_replies` _Optional[Dict[str, Dict[str, Type[Model]]]]_ - Dictionary of allowed reply digests
  for each type of incoming message.
- `_message_received` _Optional[MsgDigest]_ - The message digest received.
- `_protocol` _Optional[Tuple[str, Protocol]]_ - The supported protocol digest
  and the corresponding protocol.



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L667)
```python
def __init__(message_received: MsgDigest,
             queries: Optional[Dict[str, asyncio.Future]] = None,
             replies: Optional[Dict[str, Dict[str, Type[Model]]]] = None,
             protocol: Optional[Tuple[str, Protocol]] = None,
             **kwargs)
```

Initialize the ExternalContext instance and attributes needed from the InternalContext.

**Arguments**:

- `message_received` _MsgDigest_ - The optional message digest received.
- `queries` _Dict[str, asyncio.Future]_ - Dictionary mapping query senders to their
  response Futures.
- `replies` _Optional[Dict[str, Dict[str, Type[Model]]]]_ - Dictionary of allowed replies
  for each type of incoming message.
- `protocol` _Optional[Tuple[str, Protocol]]_ - The optional Tuple of protocols.



#### send[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L716)
```python
async def send(destination: str,
               message: Model,
               timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS) -> MsgStatus
```

Send a message to the specified destination.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `timeout` _Optional[int]_ - The optional timeout for sending the message, in seconds.
  

**Returns**:

- `MsgStatus` - The delivery status of the message.

