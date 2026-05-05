

# src.uagents.dispatch



## PendingResponse Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dispatch.py#L15)

```python
@dataclass
class PendingResponse()
```



#### accepts[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dispatch.py#L20)
```python
def accepts(schema_digest: str) -> bool
```

Whether an incoming message should resolve this response slot.



## Sink Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dispatch.py#L29)

```python
class Sink(ABC)
```

Abstract base class for sinks that handle messages.



## Dispatcher Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/dispatch.py#L47)

```python
class Dispatcher()
```

Dispatches incoming messages to internal sinks.

