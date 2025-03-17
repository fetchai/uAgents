

# src.uagents.envelope

Agent Envelope.



## Envelope Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L22)

```python
class Envelope(BaseModel)
```

Represents an envelope for message communication between agents.

**Attributes**:

- `version` _int_ - The envelope version.
- `sender` _str_ - The sender's address.
- `target` _str_ - The target's address.
- `session` _UUID4_ - The session UUID that persists for back-and-forth
  dialogues between agents.
- `schema_digest` _str_ - The schema digest for the enclosed message.
- `protocol_digest` _str | None_ - The digest of the protocol associated with the message
  (optional).
- `payload` _str | None_ - The encoded message payload of the envelope (optional).
- `expires` _int | None_ - The expiration timestamp (optional).
- `nonce` _int | None_ - The nonce value (optional).
- `signature` _str | None_ - The envelope signature (optional).



#### encode_payload[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L52)
```python
def encode_payload(value: JsonStr) -> None
```

Encode the payload value and store it in the envelope.

**Arguments**:

- `value` _JsonStr_ - The payload value to be encoded.



#### decode_payload[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L61)
```python
def decode_payload() -> str
```

Decode and retrieve the payload value from the envelope.

**Returns**:

- `str` - The decoded payload value, or '' if payload is not present.



#### sign[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L73)
```python
def sign(signing_fn: Callable) -> None
```

Sign the envelope using the provided signing function.

**Arguments**:

- `signing_fn` _callback_ - The callback used for signing.



#### verify[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L85)
```python
def verify() -> bool
```

Verify the envelope's signature.

**Returns**:

- `bool` - True if the signature is valid.
  

**Raises**:

- `ValueError` - If the signature is missing.
- `ecdsa.BadSignatureError` - If the signature is invalid.



## EnvelopeHistory Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L152)

```python
class EnvelopeHistory()
```

Stores message history for an agent optionally using cache and/or storage.



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L233)
```python
def __init__(storage: StorageAPI,
             use_cache: bool = True,
             use_storage: bool = False,
             logger: logging.Logger | None = None,
             retention_period: int = MESSAGE_HISTORY_RETENTION_SECONDS,
             message_limit: int = MESSAGE_HISTORY_MESSAGE_LIMIT)
```

Initialize the message history.

**Arguments**:

- `storage` _StorageAPI_ - The storage API to use.
- `use_cache` _bool_ - Whether to use the cache.
- `use_storage` _bool_ - Whether to use the storage.
- `logger` _logging.Logger | None_ - The logger to use.
- `retention_period` _int_ - The retention period in seconds.
- `message_limit` _int_ - The message limit.



#### add_entry[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L183)
```python
def add_entry(entry: EnvelopeHistoryEntry) -> None
```

Add an envelope entry to the message history.

**Arguments**:

- `entry` _EnvelopeHistoryEntry_ - The entry to add.



#### get_cached_messages[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L215)
```python
def get_cached_messages() -> EnvelopeHistoryResponse
```

Retrieve the cached message history.

**Returns**:

- `EnvelopeHistoryResponse` - The cached message history.



#### get_session_messages[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L226)
```python
def get_session_messages(session: UUID4) -> list[EnvelopeHistoryEntry]
```

Retrieve the message history for a given session.

**Arguments**:

- `session` _UUID4_ - The session UUID.
  

**Returns**:

- `list[EnvelopeHistoryEntry]` - The message history for the session.



#### apply_retention_policy[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L242)
```python
def apply_retention_policy() -> None
```

Remove entries older than retention period.

