

# src.uagents.types



## MsgInfo Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L54)

```python
class MsgInfo(BaseModel)
```

Represents a message digest containing a message and its schema digest and sender.

**Attributes**:

- `message` _Any_ - The message content.
- `sender` _str_ - The address of the sender of the message.
- `schema_digest` _str_ - The schema digest of the message.



## EnvelopeHistory Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L105)

```python
class EnvelopeHistory()
```

Stores message history for an agent optionally using cache and/or storage.



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L110)
```python
def __init__(storage: StorageAPI,
             use_cache: bool = True,
             use_storage: bool = False,
             logger: logging.Logger | None = None,
             retention_period: int = MESSAGE_HISTORY_RETENTION_SECONDS,
             message_limit: int = MESSAGE_HISTORY_MESSAGE_LIMIT) -> None
```

Initialize the message history.

**Arguments**:

- `storage` _StorageAPI_ - The storage API to use.
- `use_cache` _bool_ - Whether to use the cache.
- `use_storage` _bool_ - Whether to use the storage.
- `logger` _logging.Logger | None_ - The logger to use.
- `retention_period` _int_ - The retention period in seconds.
- `message_limit` _int_ - The message limit.



#### add_entry[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L136)
```python
def add_entry(entry: EnvelopeHistoryEntry) -> None
```

Add an envelope entry to the message history.

**Arguments**:

- `entry` _EnvelopeHistoryEntry_ - The entry to add.



#### get_cached_messages[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L177)
```python
def get_cached_messages() -> EnvelopeHistoryResponse
```

Retrieve the cached message history.

**Returns**:

- `EnvelopeHistoryResponse` - The cached message history.



#### get_session_messages[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L188)
```python
def get_session_messages(session: UUID4) -> list[EnvelopeHistoryEntry]
```

Retrieve the message history for a given session.

**Arguments**:

- `session` _UUID4_ - The session UUID.
  

**Returns**:

- `list[EnvelopeHistoryEntry]` - The message history for the session.



#### apply_retention_policy[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L203)
```python
def apply_retention_policy() -> None
```

Remove entries older than retention period.

