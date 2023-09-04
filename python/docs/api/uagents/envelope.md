<a id="src.uagents.envelope"></a>

# src.uagents.envelope

Agent Envelope.

<a id="src.uagents.envelope.Envelope"></a>

## Envelope Objects

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
- `schema_digest` _str_ - The schema digest for the enclosed message (alias for protocol).
- `protocol_digest` _Optional[str]_ - The digest of the protocol associated with the message
  (optional).
- `payload` _Optional[str]_ - The encoded message payload of the envelope (optional).
- `expires` _Optional[int]_ - The expiration timestamp (optional).
- `nonce` _Optional[int]_ - The nonce value (optional).
- `signature` _Optional[str]_ - The envelope signature (optional).

<a id="src.uagents.envelope.Envelope.encode_payload"></a>

#### encode`_`payload

```python
def encode_payload(value: JsonStr)
```

Encode the payload value and store it in the envelope.

**Arguments**:

- `value` _JsonStr_ - The payload value to be encoded.

<a id="src.uagents.envelope.Envelope.decode_payload"></a>

#### decode`_`payload

```python
def decode_payload() -> Optional[Any]
```

Decode and retrieve the payload value from the envelope.

**Returns**:

- `Optional[Any]` - The decoded payload value, or None if payload is not present.

<a id="src.uagents.envelope.Envelope.sign"></a>

#### sign

```python
def sign(identity: Identity)
```

Sign the envelope using the provided identity.

**Arguments**:

- `identity` _Identity_ - The identity used for signing.

<a id="src.uagents.envelope.Envelope.verify"></a>

#### verify

```python
def verify() -> bool
```

Verify the envelope's signature.

**Returns**:

- `bool` - True if the signature is valid, False otherwise.

