

# src.uagents.communication

Agent dispatch of exchange envelopes and synchronous messages.



## Dispenser Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L24)

```python
class Dispenser()
```

Dispenses messages externally.



#### add_envelope[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L35)
```python
def add_envelope(envelope: Envelope,
                 endpoints: List[str],
                 response_future: asyncio.Future,
                 sync: bool = False)
```

Add an envelope to the dispenser.

**Arguments**:

- `envelope` _Envelope_ - The envelope to send.
- `endpoints` _List[str]_ - The endpoints to send the envelope to.
- `response_future` _asyncio.Future_ - The future to set the response on.
- `sync` _bool, optional_ - True if the message is synchronous. Defaults to False.



#### run[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L53)
```python
async def run()
```

Run the dispenser routine.



#### dispatch_local_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L75)
```python
async def dispatch_local_message(sender: str, destination: str,
                                 schema_digest: str, message: JsonStr,
                                 session_id: uuid.UUID) -> MsgStatus
```

Process a message locally.



#### send_exchange_envelope[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L99)
```python
async def send_exchange_envelope(
        envelope: Envelope,
        endpoints: List[str],
        sync: bool = False) -> Union[MsgStatus, Envelope]
```

Method to send an exchange envelope.

**Arguments**:

- `envelope` _Envelope_ - The envelope to send.
- `resolver` _Optional[Resolver], optional_ - The resolver to use. Defaults to None.
- `sync` _bool, optional_ - True if the message is synchronous. Defaults to False.
  

**Returns**:

  Union[MsgStatus, Envelope]: Either the status of the message or the response envelope.



#### dispatch_sync_response_envelope[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L168)
```python
async def dispatch_sync_response_envelope(
        env: Envelope, endpoint: str) -> Union[MsgStatus, Envelope]
```

Dispatch a synchronous response envelope locally.



#### send_message_raw[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L187)
```python
async def send_message_raw(
        destination: str,
        message_schema_digest: str,
        message_body: JsonStr,
        response_type: Optional[Type[Model]] = None,
        sender: Optional[Union[Identity, str]] = None,
        resolver: Optional[Resolver] = None,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        sync: bool = False) -> Union[Model, JsonStr, MsgStatus, Envelope]
```

Standalone function to send a message to an agent.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message_schema_digest` _str_ - The schema digest of the message.
- `message_body` _JsonStr_ - The JSON-formatted message to be sent.
- `response_type` _Optional[Type[Model]]_ - The optional type of the response message.
- `sender` _Optional[Union[Identity, str]]_ - The optional sender identity or user address.
- `resolver` _Optional[Resolver]_ - The optional resolver for address-to-endpoint resolution.
- `timeout` _int_ - The timeout for the message response in seconds. Defaults to 30.
- `sync` _bool_ - True if the message is synchronous.
  

**Returns**:

  Union[Model, JsonStr, MsgStatus, Envelope]: On success, if the response type is provided,
  the response message is returned with that type. Otherwise, the JSON message is returned.
  If the sender is a user address, the response envelope is returned.
  On failure, a message status is returned.



#### send_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L265)
```python
async def send_message(
        destination: str,
        message: Model,
        response_type: Optional[Type[Model]] = None,
        sender: Optional[Union[Identity, str]] = None,
        resolver: Optional[Resolver] = None,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
        sync: bool = False) -> Union[Model, JsonStr, MsgStatus, Envelope]
```

Standalone function to send a message to an agent.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `response_type` _Optional[Type[Model]]_ - The optional type of the response message.
- `sender` _Optional[Union[Identity, str]]_ - The optional sender identity or user address.
- `resolver` _Optional[Resolver]_ - The optional resolver for address-to-endpoint resolution.
- `timeout` _int_ - The timeout for the message response in seconds. Defaults to 30.
- `sync` _bool_ - True if the message is synchronous.
  

**Returns**:

  Union[Model, JsonStr, MsgStatus, Envelope]: On success, if the response type is provided,
  the response message is returned with that type. Otherwise, the JSON message is returned.
  If the sender is a user address, the response envelope is returned.
  On failure, a message status is returned.



#### send_sync_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L304)
```python
async def send_sync_message(
    destination: str,
    message: Model,
    response_type: Optional[Type[Model]] = None,
    sender: Optional[Union[Identity, str]] = None,
    resolver: Optional[Resolver] = None,
    timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS
) -> Union[Model, JsonStr, MsgStatus, Envelope]
```

Standalone function to send a synchronous message to an agent.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `response_type` _Optional[Type[Model]]_ - The optional type of the response message.
- `sender` _Optional[Union[Identity, str]]_ - The optional sender identity or user address.
- `resolver` _Optional[Resolver]_ - The optional resolver for address-to-endpoint resolution.
- `timeout` _int_ - The timeout for the message response in seconds. Defaults to 30.
- `sync` _bool_ - True if the message is synchronous.
  

**Returns**:

  Union[Model, JsonStr, MsgStatus, Envelope]: On success, if the response type is provided,
  the response message is returned with that type. Otherwise, the JSON message is returned.
  If the sender is a user address, the response envelope is returned.
  On failure, a message status is returned.



#### enclose_response[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L335)
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



#### enclose_response_raw[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/communication.py#L356)
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

