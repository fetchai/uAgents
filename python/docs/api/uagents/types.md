<a id="src.uagents.types"></a>

# src.uagents.types

<a id="src.uagents.types.AgentGeolocation"></a>

## AgentGeolocation Objects

```python
class AgentGeolocation(BaseModel)
```

<a id="src.uagents.types.AgentGeolocation.serialize_precision"></a>

#### serialize`_`precision

```python
@field_validator("latitude", "longitude")
@classmethod
def serialize_precision(cls, val: float) -> float
```

Round the latitude and longitude to 6 decimal places.
Equivalent to 0.11m precision.

<a id="src.uagents.types.AgentMetadata"></a>

## AgentMetadata Objects

```python
class AgentMetadata(BaseModel)
```

Model used to validate metadata for an agent.

Framework specific fields will be added here to ensure valid serialization.
Additional fields will simply be passed through.

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

