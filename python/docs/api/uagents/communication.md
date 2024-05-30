<a id="src.uagents.communication"></a>

# src.uagents.communication

Agent dispatch of exchange envelopes and synchronous messages.

<a id="src.uagents.communication.DeliveryStatus"></a>

## DeliveryStatus Objects

```python
class DeliveryStatus(str, Enum)
```

Delivery status of a message.

<a id="src.uagents.communication.MsgDigest"></a>

## MsgDigest Objects

```python
@dataclass
class MsgDigest()
```

Represents a message digest containing a message and its schema digest.

**Attributes**:

- `message` _Any_ - The message content.
- `schema_digest` _str_ - The schema digest of the message.

<a id="src.uagents.communication.MsgStatus"></a>

## MsgStatus Objects

```python
@dataclass
class MsgStatus()
```

Represents the status of a sent message.

**Attributes**:

- `status` _str_ - The delivery status of the message {'sent', 'delivered', 'failed'}.
- `detail` _str_ - The details of the message delivery.
- `destination` _str_ - The destination address of the message.
- `endpoint` _str_ - The endpoint the message was sent to.
- `session` _Optional[uuid.UUID]_ - The session ID of the message.

<a id="src.uagents.communication.Dispenser"></a>

## Dispenser Objects

```python
class Dispenser()
```

Dispenses messages externally.

<a id="src.uagents.communication.Dispenser.add_envelope"></a>

#### add`_`envelope

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

<a id="src.uagents.communication.Dispenser.run"></a>

#### run

```python
async def run()
```

Run the dispenser routine.

<a id="src.uagents.communication.dispatch_local_message"></a>

#### dispatch`_`local`_`message

```python
async def dispatch_local_message(sender: str, destination: str,
                                 schema_digest: str, message: JsonStr,
                                 session_id: uuid.UUID) -> MsgStatus
```

Process a message locally.

<a id="src.uagents.communication.send_exchange_envelope"></a>

#### send`_`exchange`_`envelope

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

<a id="src.uagents.communication.dispatch_sync_response_envelope"></a>

#### dispatch`_`sync`_`response`_`envelope

```python
async def dispatch_sync_response_envelope(env: Envelope) -> MsgStatus
```

Dispatch a synchronous response envelope locally.

<a id="src.uagents.communication.send_sync_message"></a>

#### send`_`sync`_`message

```python
async def send_sync_message(
        destination: str,
        message: Model,
        response_type: Optional[Type[Model]] = None,
        sender: Optional[Identity] = None,
        resolver: Optional[Resolver] = None,
        timeout: int = 30) -> Union[Model, JsonStr, MsgStatus]
```

Standalone function to send a synchronous message to an agent.

**Arguments**:

- `destination` _str_ - The destination address to send the message to.
- `message` _Model_ - The message to be sent.
- `response_type` _Type[Model]_ - The optional type of the response message.
- `sender` _Identity_ - The optional sender identity (defaults to a generated identity).
- `resolver` _Resolver_ - The optional resolver for address-to-endpoint resolution.
- `timeout` _int_ - The optional timeout for the message response in seconds.
  

**Returns**:

  Union[Model, JsonStr, MsgStatus]: On success, if the response type is provided, the response
  message is returned with that type. Otherwise, the JSON message is returned. On failure, a
  message status is returned.

