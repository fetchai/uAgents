<a id="src.uagents.protocol"></a>

# src.uagents.protocol

Exchange Protocol

<a id="src.uagents.protocol.Protocol"></a>

## Protocol Objects

```python
class Protocol()
```

The Protocol class encapsulates a particular set of functionalities for an agent.
It typically relates to the exchange of messages between agents for executing some task.
It includes the message (model) types it supports, the allowed replies, and the
interval message handlers that define the logic of the protocol.

<a id="src.uagents.protocol.Protocol.__init__"></a>

#### `__`init`__`

```python
def __init__(name: Optional[str] = None, version: Optional[str] = None)
```

Initialize a Protocol instance.

**Arguments**:

- `name` _Optional[str], optional_ - The name of the protocol. Defaults to None.
- `version` _Optional[str], optional_ - The version of the protocol. Defaults to None.

<a id="src.uagents.protocol.Protocol.intervals"></a>

#### intervals

```python
@property
def intervals()
```

Property to access the interval handlers.

**Returns**:

  List[Tuple[IntervalCallback, float]]: List of interval handlers and their periods.

<a id="src.uagents.protocol.Protocol.models"></a>

#### models

```python
@property
def models()
```

Property to access the registered models.

**Returns**:

  Dict[str, Type[Model]]: Dictionary of registered models with schema digests as keys.

<a id="src.uagents.protocol.Protocol.replies"></a>

#### replies

```python
@property
def replies()
```

Property to access the registered replies.

**Returns**:

  Dict[str, Dict[str, Type[Model]]]: Dictionary mapping message schema digests to their
  allowed replies.

<a id="src.uagents.protocol.Protocol.interval_messages"></a>

#### interval`_`messages

```python
@property
def interval_messages()
```

Property to access the interval message digests.

**Returns**:

- `Set[str]` - Set of message digests that may be sent by interval handlers.

<a id="src.uagents.protocol.Protocol.signed_message_handlers"></a>

#### signed`_`message`_`handlers

```python
@property
def signed_message_handlers()
```

Property to access the signed message handlers.

**Returns**:

  Dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.

<a id="src.uagents.protocol.Protocol.unsigned_message_handlers"></a>

#### unsigned`_`message`_`handlers

```python
@property
def unsigned_message_handlers()
```

Property to access the unsigned message handlers.

**Returns**:

  Dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.

<a id="src.uagents.protocol.Protocol.name"></a>

#### name

```python
@property
def name()
```

Property to access the protocol name.

**Returns**:

- `str` - The protocol name.

<a id="src.uagents.protocol.Protocol.version"></a>

#### version

```python
@property
def version()
```

Property to access the protocol version.

**Returns**:

- `str` - The protocol version.

<a id="src.uagents.protocol.Protocol.canonical_name"></a>

#### canonical`_`name

```python
@property
def canonical_name()
```

Property to access the canonical name of the protocol ('name:version').

**Returns**:

- `str` - The canonical name of the protocol.

<a id="src.uagents.protocol.Protocol.digest"></a>

#### digest

```python
@property
def digest()
```

Property to access the digest of the protocol's manifest.

**Returns**:

- `str` - The digest of the protocol's manifest.

<a id="src.uagents.protocol.Protocol.on_interval"></a>

#### on`_`interval

```python
def on_interval(period: float,
                messages: Optional[Union[Type[Model],
                                         Set[Type[Model]]]] = None)
```

Decorator to register an interval handler for the protocol.

**Arguments**:

- `period` _float_ - The interval period in seconds.
- `messages` _Optional[Union[Type[Model], Set[Type[Model]]]], optional_ - The associated
  message types. Defaults to None.
  

**Returns**:

- `Callable` - The decorator to register the interval handler.

<a id="src.uagents.protocol.Protocol.on_query"></a>

#### on`_`query

```python
def on_query(model: Type[Model],
             replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None)
```

Decorator to register a query handler for the protocol.

**Arguments**:

- `model` _Type[Model]_ - The message model type.
- `replies` _Optional[Union[Type[Model], Set[Type[Model]]]], optional_ - The associated
  reply types. Defaults to None.
  

**Returns**:

- `Callable` - The decorator to register the query handler.

<a id="src.uagents.protocol.Protocol.on_message"></a>

#### on`_`message

```python
def on_message(model: Type[Model],
               replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
               allow_unverified: Optional[bool] = False)
```

Decorator to register a message handler for the protocol.

**Arguments**:

- `model` _Type[Model]_ - The message model type.
- `replies` _Optional[Union[Type[Model], Set[Type[Model]]]], optional_ - The associated
  reply types. Defaults to None.
- `allow_unverified` _Optional[bool], optional_ - Whether to allow unverified messages.
  Defaults to False.
  

**Returns**:

- `Callable` - The decorator to register the message handler.

<a id="src.uagents.protocol.Protocol.manifest"></a>

#### manifest

```python
def manifest() -> Dict[str, Any]
```

Generate the protocol's manifest, a long-form machine readable description of the
protocol details and interface.

**Returns**:

  Dict[str, Any]: The protocol's manifest.

<a id="src.uagents.protocol.Protocol.compute_digest"></a>

#### compute`_`digest

```python
@staticmethod
def compute_digest(manifest: Dict[str, Any]) -> str
```

Compute the digest of a given manifest.

**Arguments**:

- `manifest` _Dict[str, Any]_ - The manifest to compute the digest for.
  

**Returns**:

- `str` - The computed digest.

