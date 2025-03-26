

# src.uagents.protocol

Exchange Protocol



## Protocol Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L18)

```python
class Protocol()
```

The Protocol class encapsulates a particular set of functionalities for an agent.
It typically relates to the exchange of messages between agents for executing some task.
It includes the message (model) types it supports, the allowed replies, and the
interval message handlers that define the logic of the protocol.



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L26)
```python
def __init__(name: str | None = None,
             version: str | None = None,
             spec: ProtocolSpecification | None = None,
             role: str | None = None) -> None
```

Initialize a Protocol instance.

**Arguments**:

- `name` _str | None_ - The name of the protocol. Defaults to None.
- `version` _str | None_ - The version of the protocol. Defaults to None.
- `spec` _ProtocolSpecification | None_ - The protocol specification. Defaults to None.
- `role` _str | None_ - The role that the protocol will implement. Defaults to None.



#### intervals[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L59)
```python
@property
def intervals() -> list[tuple[IntervalCallback, float]]
```

Property to access the interval handlers.

**Returns**:

  list[tuple[IntervalCallback, float]]: List of interval handlers and their periods.



#### models[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L69)
```python
@property
def models() -> dict[str, type[Model]]
```

Property to access the registered models.

**Returns**:

  dict[str, type[Model]]: Dictionary of registered models with schema digests as keys.



#### replies[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L79)
```python
@property
def replies() -> dict[str, dict[str, type[Model]]]
```

Property to access the registered replies.

**Returns**:

  dict[str, dict[str, type[Model]]]: Dictionary mapping message schema digests to their
  allowed replies.



#### interval_messages[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L90)
```python
@property
def interval_messages() -> set[str]
```

Property to access the interval message digests.

**Returns**:

- `set[str]` - Set of message digests that may be sent by interval handlers.



#### signed_message_handlers[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L100)
```python
@property
def signed_message_handlers() -> dict[str, MessageCallback]
```

Property to access the signed message handlers.

**Returns**:

  dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.



#### unsigned_message_handlers[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L110)
```python
@property
def unsigned_message_handlers() -> dict[str, MessageCallback]
```

Property to access the unsigned message handlers.

**Returns**:

  dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.



#### name[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L120)
```python
@property
def name() -> str
```

Property to access the protocol name.

**Returns**:

- `str` - The protocol name.



#### version[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L130)
```python
@property
def version() -> str
```

Property to access the protocol version.

**Returns**:

- `str` - The protocol version.



#### canonical_name[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L140)
```python
@property
def canonical_name() -> str
```

Property to access the canonical name of the protocol ('name:version').

**Returns**:

- `str` - The canonical name of the protocol.



#### digest[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L150)
```python
@property
def digest() -> str
```

Property to access the digest of the protocol's manifest.

**Returns**:

- `str` - The digest of the protocol's manifest.



#### spec[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L160)
```python
@property
def spec() -> ProtocolSpecification
```

Property to access the protocol specification.

**Returns**:

- `ProtocolSpecification` - The protocol specification.



#### on_interval[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L236)
```python
def on_interval(
        period: float,
        messages: type[Model] | set[type[Model]] | None = None) -> Callable
```

Decorator to register an interval handler for the protocol.

**Arguments**:

- `period` _float_ - The interval period in seconds.
- `messages` _type[Model] | set[type[Model]] | None_ - The associated message types.
  

**Returns**:

- `Callable` - The decorator to register the interval handler.



#### on_query[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L288)
```python
@deprecated(
    "on_query is deprecated and will be removed in a future release, use on_rest instead."
)
def on_query(
        model: type[Model],
        replies: type[Model] | set[type[Model]] | None = None) -> Callable
```

Decorator to register a query handler for the protocol.

**Arguments**:

- `model` _type[Model]_ - The message model type.
- `replies` _type[Model] | set[type[Model]] | None_ - The associated reply types.
  

**Returns**:

- `Callable` - The decorator to register the query handler.



#### on_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L308)
```python
def on_message(model: type[Model],
               replies: type[Model] | set[type[Model]] | None = None,
               allow_unverified: bool = False) -> Callable
```

Decorator to register a message handler for the protocol.

**Arguments**:

- `model` _type[Model]_ - The message model type.
- `replies` _type[Model] | set[type[Model]] | None_ - The associated reply types.
- `allow_unverified` _bool, optional_ - Whether to allow unverified messages.
  

**Returns**:

- `Callable` - The decorator to register the message handler.



#### manifest[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L383)
```python
def manifest() -> dict[str, Any]
```

Generate the protocol's manifest, a long-form machine readable description of the
protocol details and interface.

**Returns**:

  dict[str, Any]: The protocol's manifest.



#### verify[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L393)
```python
def verify() -> bool
```

Check if the protocol implements all interactions of its specification.

**Returns**:

- `bool` - True if the protocol implements the role, False otherwise.



#### compute_digest[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L423)
```python
@staticmethod
def compute_digest(manifest: dict[str, Any]) -> str
```

Compute the digest of a given manifest.

**Arguments**:

- `manifest` _dict[str, Any]_ - The manifest to compute the digest for.
  

**Returns**:

- `str` - The computed digest.

