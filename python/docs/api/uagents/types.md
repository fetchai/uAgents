<a id="src.uagents.types"></a>

# src.uagents.types

<a id="src.uagents.types.DeliveryStatus"></a>

## DeliveryStatus Objects

```python
class DeliveryStatus(str, Enum)
```

Delivery status of a message.

<a id="src.uagents.types.MsgDigest"></a>

## MsgDigest Objects

```python
@dataclass
class MsgDigest()
```

Represents a message digest containing a message and its schema digest.

**Attributes**:

- `message` _Any_ - The message content.
- `schema_digest` _str_ - The schema digest of the message.

<a id="src.uagents.types.MsgStatus"></a>

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

