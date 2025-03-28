

# src.uagents.context

Agent Context and Message Handling



## Context Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L37)

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
- `session_history` - Get the message history associated with the context session.
  send(destination, message, timeout): Send a message to a destination.
  send_raw(destination, json_message, schema_digest, message_type, timeout):
  Send a message with the provided schema digest to a destination.



#### agent[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L59)
```python
@property
@abstractmethod
def agent() -> "AgentRepresentation"
```

Get the agent representation associated with the context.

**Returns**:

- `AgentRepresentation` - The agent representation.



#### storage[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L70)
```python
@property
@abstractmethod
def storage() -> KeyValueStore
```

Get the key-value store associated with the context.

**Returns**:

- `KeyValueStore` - The key-value store.



#### ledger[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L81)
```python
@property
@abstractmethod
def ledger() -> LedgerClient
```

Get the ledger client associated with the context.

**Returns**:

- `LedgerClient` - The ledger client.



#### logger[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L92)
```python
@property
@abstractmethod
def logger() -> logging.Logger
```

Get the logger instance associated with the context.

**Returns**:

- `logging.Logger` - The logger instance.



#### session[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L103)
```python
@property
@abstractmethod
def session() -> uuid.UUID
```

Get the session UUID associated with the context.

**Returns**:

- `uuid.UUID` - The session UUID.



#### get_agents_by_protocol[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L114)
```python
@abstractmethod
def get_agents_by_protocol(protocol_digest: str,
                           limit: int = DEFAULT_SEARCH_LIMIT,
                           logger: logging.Logger | None = None) -> list[str]
```

Retrieve a list of agent addresses using a specific protocol digest.

This method queries the Almanac API to retrieve a list of agent addresses
that are associated with a given protocol digest. The list can be optionally
limited to a specified number of addresses.

**Arguments**:

- `protocol_digest` _str_ - The protocol digest to search for, starting with "proto:".
- `limit` _int, optional_ - The maximum number of agent addresses to return.
  

**Returns**:

- `list[str]` - A list of agent addresses using the specified protocol digest.



#### broadcast[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L136)
```python
@abstractmethod
async def broadcast(
        destination_protocol: str,
        message: Model,
        limit: int = DEFAULT_SEARCH_LIMIT,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS) -> list[MsgStatus]
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

- `list[MsgStatus]` - A list of message delivery statuses.



#### session_history[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L161)
```python
@abstractmethod
def session_history() -> list[EnvelopeHistoryEntry] | None
```

Get the message history associated with the context session.

**Returns**:

  list[EnvelopeHistoryEntry] | None: The message history.



#### send[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L171)
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
- `timeout` _int, optional_ - The timeout for sending the message, in seconds.
  

**Returns**:

- `MsgStatus` - The delivery status of the message.



#### send_raw[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L191)
```python
@abstractmethod
async def send_raw(
        destination: str,
        message_schema_digest: str,
        message_body: JsonStr,
        sync: bool = False,
        wait_for_response: bool = False,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        protocol_digest: str | None = None,
        queries: dict[str, asyncio.Future] | None = None) -> MsgStatus
```

Send a message to the specified destination where the message body and
message schema digest are sent separately.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message_schema_digest` _str_ - The schema digest of the message to be sent.
- `message_body` _JsonStr_ - The JSON-encoded message body to be sent.
- `sync` _bool_ - Whether to send the message synchronously or asynchronously.
- `wait_for_response` _bool_ - Whether to wait for a response to the message.
- `timeout` _int, optional_ - The optional timeout for sending the message, in seconds.
- `protocol_digest` _str, optional_ - The protocol digest of the message to be sent.
- `queries` _dict[str, asyncio.Future] | None_ - The dictionary of queries to resolve.
  

**Returns**:

- `MsgStatus` - The delivery status of the message.



#### send_and_receive[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L222)
```python
@abstractmethod
async def send_and_receive(
    destination: str,
    message: Model,
    response_type: type[Model],
    sync: bool = False,
    timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS
) -> tuple[Model | None, MsgStatus]
```

Send a message to the specified destination and receive a response.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `response_type` _type[Model]_ - The type of the response message.
- `sync` _bool_ - Whether to send the message synchronously or asynchronously.
- `timeout` _int_ - The timeout for sending the message, in seconds.
  

**Returns**:

  tuple[Model | None, MsgStatus]: The response message if received and delivery status



#### send_wallet_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L246)
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



## InternalContext Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L267)

```python
class InternalContext(Context)
```

Represents the agent internal context for proactive behaviour.



#### session[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L311)
```python
@property
def session() -> uuid.UUID
```

Get the session UUID associated with the context.

**Returns**:

- `uuid.UUID` - The session UUID.



#### outbound_messages[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L321)
```python
@property
def outbound_messages() -> dict[str, tuple[JsonStr, str]]
```

Get the dictionary of outbound messages associated with the context.

**Returns**:

  dict[str, tuple[JsonStr, str]]: The dictionary of outbound messages.



#### session_history[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L331)
```python
def session_history() -> list[EnvelopeHistoryEntry] | None
```

Get the message history associated with the context session.

**Returns**:

  list[EnvelopeHistoryEntry] | None: The session history.



#### send[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L417)
```python
async def send(destination: str,
               message: Model,
               timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS) -> MsgStatus
```

This is the pro-active send method which is used in on_event and
on_interval methods. In these methods, interval messages are set but
we don't have access properties that are only necessary in re-active
contexts, like 'replies', 'message_received', or 'protocol'.



#### send_and_receive[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L589)
```python
async def send_and_receive(
    destination: str,
    message: Model,
    response_type: type[Model],
    sync: bool = False,
    timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS
) -> tuple[Model | None, MsgStatus]
```

Send a message to the specified destination and receive a response.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `response_type` _type[Model]_ - The type of the response message.
- `sync` _bool_ - Whether to send the message synchronously or asynchronously.
- `timeout` _int_ - The timeout for sending the message, in seconds.
  

**Returns**:

  tuple[Model | None, MsgStatus]: The response message if received and delivery status



## ExternalContext Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L675)

```python
class ExternalContext(InternalContext)
```

Represents the reactive context in which messages are handled and processed.

**Attributes**:

- `_message_received` _MsgInfo_ - The received message.
- `_queries` _dict[str, asyncio.Future] | None_ - dictionary mapping query senders to their
  response Futures.
- `_replies` _dict[str, dict[str, type[Model]]] | None_ - Dictionary of allowed reply digests
  for each type of incoming message.
- `_protocol` _tuple[str, Protocol] | None_ - The supported protocol digest
  and the corresponding protocol.



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L689)
```python
def __init__(message_received: MsgInfo,
             queries: dict[str, asyncio.Future] | None = None,
             replies: dict[str, dict[str, type[Model]]] | None = None,
             protocol: tuple[str, "Protocol"] | None = None,
             **kwargs)
```

Initialize the ExternalContext instance and attributes needed from the InternalContext.

**Arguments**:

- `message_received` _MsgInfo_ - Information about the received message.
- `queries` _dict[str, asyncio.Future]_ - Dictionary mapping query senders to their
  response Futures.
- `replies` _dict[str, dict[str, type[Model]]] | None_ - Dictionary of allowed replies
  for each type of incoming message.
- `protocol` _tuple[str, Protocol] | None_ - The optional tuple of protocols.



#### validate_replies[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L714)
```python
def validate_replies() -> None
```

If the context specifies replies, ensure that a valid reply was sent.



#### send[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/context.py#L739)
```python
async def send(destination: str,
               message: Model,
               timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS) -> MsgStatus
```

Send a message to the specified destination.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `timeout` _int | None_ - The optional timeout for sending the message, in seconds.
  

**Returns**:

- `MsgStatus` - The delivery status of the message.

