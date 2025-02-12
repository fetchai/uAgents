

# src.uagents.protocol

Exchange Protocol



## Protocol Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L13)

```python
class Protocol()
```

The Protocol class encapsulates a particular set of functionalities for an agent.
It typically relates to the exchange of messages between agents for executing some task.
It includes the message (model) types it supports, the allowed replies, and the
interval message handlers that define the logic of the protocol.



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L22)
```python
def __init__(name: Optional[str] = None, version: Optional[str] = None)
```

Initialize a Protocol instance.

**Arguments**:

- `name` _Optional[str], optional_ - The name of the protocol. Defaults to None.
- `version` _Optional[str], optional_ - The version of the protocol. Defaults to None.



#### intervals[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L41)
```python
@property
def intervals()
```

Property to access the interval handlers.

**Returns**:

  List[Tuple[IntervalCallback, float]]: List of interval handlers and their periods.



#### models[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L51)
```python
@property
def models()
```

Property to access the registered models.

**Returns**:

  Dict[str, Type[Model]]: Dictionary of registered models with schema digests as keys.



#### replies[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L61)
```python
@property
def replies()
```

Property to access the registered replies.

**Returns**:

  Dict[str, Dict[str, Type[Model]]]: Dictionary mapping message schema digests to their
  allowed replies.



#### interval_messages[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L72)
```python
@property
def interval_messages()
```

Property to access the interval message digests.

**Returns**:

- `Set[str]` - Set of message digests that may be sent by interval handlers.



#### signed_message_handlers[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L82)
```python
@property
def signed_message_handlers()
```

Property to access the signed message handlers.

**Returns**:

  Dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.



#### unsigned_message_handlers[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L92)
```python
@property
def unsigned_message_handlers()
```

Property to access the unsigned message handlers.

**Returns**:

  Dict[str, MessageCallback]: Dictionary mapping message schema digests to their handlers.



#### name[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L102)
```python
@property
def name()
```

Property to access the protocol name.

**Returns**:

- `str` - The protocol name.



#### version[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L112)
```python
@property
def version()
```

Property to access the protocol version.

**Returns**:

- `str` - The protocol version.



#### canonical_name[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L122)
```python
@property
def canonical_name()
```

Property to access the canonical name of the protocol ('name:version').

**Returns**:

- `str` - The canonical name of the protocol.



#### digest[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L132)
```python
@property
def digest()
```

Property to access the digest of the protocol's manifest.

**Returns**:

- `str` - The digest of the protocol's manifest.



#### on_interval[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L142)
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



#### on_query[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L195)
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



#### on_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L213)
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



#### manifest[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L276)
```python
def manifest() -> Dict[str, Any]
```

Generate the protocol's manifest, a long-form machine readable description of the
protocol details and interface.

**Returns**:

  Dict[str, Any]: The protocol's manifest.



#### compute_digest[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/protocol.py#L336)
```python
@staticmethod
def compute_digest(manifest: Dict[str, Any]) -> str
```

Compute the digest of a given manifest.

**Arguments**:

- `manifest` _Dict[str, Any]_ - The manifest to compute the digest for.
  

**Returns**:

- `str` - The computed digest.

