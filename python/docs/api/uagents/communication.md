

# src.uagents.communication

Agent dispatch of exchange envelopes and synchronous messages.



## Dispenser Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L30)

```python
class Dispenser()
```

Dispenses messages externally.



#### add_envelope[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L39)
```python
def add_envelope(envelope: Envelope,
                 endpoints: list[str],
                 response_future: asyncio.Future,
                 sync: bool = False) -> None
```

Add an envelope to the dispenser.

**Arguments**:

- `envelope` _Envelope_ - The envelope to send.
- `endpoints` _list[str]_ - The endpoints to send the envelope to.
- `response_future` _asyncio.Future_ - The future to set the response on.
- `sync` _bool_ - True if the message is synchronous. Defaults to False.



#### run[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L57)
```python
async def run() -> NoReturn
```

Run the dispenser routine.



#### dispatch_local_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L78)
```python
async def dispatch_local_message(sender: str, destination: str,
                                 schema_digest: str, message: JsonStr,
                                 session_id: uuid.UUID) -> MsgStatus
```

Process a message locally.



#### send_exchange_envelope[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L102)
```python
async def send_exchange_envelope(envelope: Envelope,
                                 endpoints: list[str],
                                 sync: bool = False) -> MsgStatus | Envelope
```

Method to send an exchange envelope.

**Arguments**:

- `envelope` _Envelope_ - The envelope to send.
- `endpoints` _list[str]_ - The endpoints to send the envelope to.
- `sync` _bool_ - True if the message is synchronous. Defaults to False.
  

**Returns**:

  MsgStatus | Envelope: Either the status of the message or the response envelope.



#### dispatch_sync_response_envelope[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L176)
```python
async def dispatch_sync_response_envelope(
        env: Envelope, endpoint: str) -> MsgStatus | Envelope
```

Dispatch a synchronous response envelope locally.



#### send_message_raw[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L198)
```python
async def send_message_raw(
        destination: str,
        message_schema_digest: str,
        message_body: JsonStr,
        response_type: type[Model] | None = None,
        sender: Identity | str | None = None,
        resolver: Resolver | None = None,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        sync: bool = False) -> Model | JsonStr | MsgStatus | Envelope
```

Standalone function to send a message to an agent.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message_schema_digest` _str_ - The schema digest of the message.
- `message_body` _JsonStr_ - The JSON-formatted message to be sent.
- `response_type` _type[Model] | None_ - The optional type of the response message.
- `sender` _Identity | str | None_ - The optional sender identity or user address.
- `resolver` _Resolver | None_ - The optional resolver for address-to-endpoint resolution.
- `timeout` _int_ - The timeout for the message response in seconds. Defaults to 30.
- `sync` _bool_ - True if the message is synchronous.
  

**Returns**:

  Model | JsonStr | MsgStatus | Envelope: On success, if the response type is provided,
  the response message is returned with that type. Otherwise, the JSON message is returned.
  If the sender is a user address, the response envelope is returned.
  On failure, a message status is returned.



#### send_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L277)
```python
async def send_message(
        destination: str,
        message: Model,
        response_type: type[Model] | None = None,
        sender: Identity | str | None = None,
        resolver: Resolver | None = None,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        sync: bool = False) -> Model | JsonStr | MsgStatus | Envelope
```

Standalone function to send a message to an agent.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `response_type` _type[Model] | None_ - The optional type of the response message.
- `sender` _Identity | str | None_ - The optional sender identity or user address.
- `resolver` _Resolver | None_ - The optional resolver for address-to-endpoint resolution.
- `timeout` _int_ - The timeout for the message response in seconds. Defaults to 30.
- `sync` _bool_ - True if the message is synchronous.
  

**Returns**:

  Model | JsonStr | MsgStatus | Envelope: On success, if the response type is provided,
  the response message is returned with that type. Otherwise, the JSON message is returned.
  If the sender is a user address, the response envelope is returned.
  On failure, a message status is returned.



#### send_sync_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L316)
```python
async def send_sync_message(
    destination: str,
    message: Model,
    response_type: type[Model] | None = None,
    sender: Identity | str | None = None,
    resolver: Resolver | None = None,
    timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS
) -> Model | JsonStr | MsgStatus | Envelope
```

Standalone function to send a synchronous message to an agent.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `response_type` _type[Model] | None_ - The optional type of the response message.
- `sender` _Identity | str | None_ - The optional sender identity or user address.
- `resolver` _Resolver | None_ - The optional resolver for address-to-endpoint resolution.
- `timeout` _int_ - The timeout for the message response in seconds. Defaults to 30.
- `sync` _bool_ - True if the message is synchronous.
  

**Returns**:

  Model | JsonStr | MsgStatus | Envelope: On success, if the response type is provided,
  the response message is returned with that type. Otherwise, the JSON message is returned.
  If the sender is a user address, the response envelope is returned.
  On failure, a message status is returned.



#### enclose_response[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L353)
```python
def enclose_response(message: Model,
                     sender: str,
                     session: UUID4,
                     target: str = "") -> JsonStr
```

Enclose a response message within an envelope.

**Arguments**:

- `message` _Model_ - The response message to enclose.
- `sender` _str_ - The sender's address.
- `session` _str_ - The session identifier.
- `target` _str_ - The target address.
  

**Returns**:

- `str` - The JSON representation of the response envelope.



#### enclose_response_raw[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L378)
```python
def enclose_response_raw(json_message: JsonStr,
                         schema_digest: str,
                         sender: str,
                         session: UUID4,
                         target: str = "") -> JsonStr
```

Enclose a raw response message within an envelope.

**Arguments**:

- `json_message` _JsonStr_ - The JSON-formatted response message to enclose.
- `schema_digest` _str_ - The schema digest of the message.
- `sender` _str_ - The sender's address.
- `session` _UUID4_ - The session identifier.
- `target` _str_ - The target address.
  

**Returns**:

- `str` - The JSON representation of the response envelope.

