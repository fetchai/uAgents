

# src.uagents.envelope

Agent Envelope.



## Envelope Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L17)

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



#### encode_payload[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L47)
```python
def encode_payload(value: JsonStr) -> None
```

Encode the payload value and store it in the envelope.

**Arguments**:

- `value` _JsonStr_ - The payload value to be encoded.



#### decode_payload[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L56)
```python
def decode_payload() -> str
```

Decode and retrieve the payload value from the envelope.

**Returns**:

- `str` - The decoded payload value, or '' if payload is not present.



#### sign[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L68)
```python
def sign(signing_fn: Callable) -> None
```

Sign the envelope using the provided signing function.

**Arguments**:

- `signing_fn` _callback_ - The callback used for signing.



#### verify[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L80)
```python
def verify() -> bool
```

Verify the envelope's signature.

**Returns**:

- `bool` - True if the signature is valid.
  

**Raises**:

- `ValueError` - If the signature is missing.
- `ecdsa.BadSignatureError` - If the signature is invalid.



## EnvelopeHistory Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L147)

```python
class EnvelopeHistory()
```

Stores message history for an agent optionally using cache and/or storage.



#### apply_retention_policy[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/envelope.py#L192)
```python
def apply_retention_policy() -> None
```

Remove entries older than 24 hours

