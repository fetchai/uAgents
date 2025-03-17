

# src.uagents.types



## AgentGeolocation Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L56)

```python
class AgentGeolocation(BaseModel)
```



#### serialize_precision

```python
@field_validator("latitude", "longitude")
@classmethod
def serialize_precision(cls, val: float) -> float
```

Round the latitude and longitude to 6 decimal places.
Equivalent to 0.11m precision.



## AgentMetadata Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L72)

```python
class AgentMetadata(BaseModel)
```

Model used to validate metadata for an agent.

Framework specific fields will be added here to ensure valid serialization.
Additional fields will simply be passed through.



## DeliveryStatus Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L88)

```python
class DeliveryStatus(str, Enum)
```

Delivery status of a message.



## MsgInfo Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L96)

```python
class MsgInfo(BaseModel)
```

Represents a message digest containing a message and its schema digest and sender.

**Attributes**:

- `message` _Any_ - The message content.
- `sender` _str_ - The address of the sender of the message.
- `schema_digest` _str_ - The schema digest of the message.



## MsgStatus Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L111)

```python
class MsgStatus(BaseModel)
```

Represents the status of a sent message.

**Attributes**:

- `status` _str_ - The delivery status of the message {'sent', 'delivered', 'failed'}.
- `detail` _str_ - The details of the message delivery.
- `destination` _str_ - The destination address of the message.
- `endpoint` _str_ - The endpoint the message was sent to.
- `session` _uuid.UUID | None_ - The session ID of the message.



## EnvelopeHistory Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L158)

```python
class EnvelopeHistory(BaseModel)
```



#### apply_retention_policy[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/types.py#L165)
```python
def apply_retention_policy() -> None
```

Remove entries older than 24 hours

