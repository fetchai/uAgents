

# src.uagents.asgi



## ASGIServer Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L40)

```python
class ASGIServer()
```

ASGI server for receiving incoming envelopes.



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L43)
```python
def __init__(port: int,
             loop: asyncio.AbstractEventLoop,
             queries: dict[str, asyncio.Future],
             logger: Logger | None = None)
```

Initialize the ASGI server.

**Arguments**:

- `port` _int_ - The port to listen on.
- `loop` _asyncio.AbstractEventLoop_ - The event loop to use.
- `queries` _dict[str, asyncio.Future]_ - The dictionary of queries to resolve.
- `logger` _Logger | None_ - The logger to use.



#### server[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L68)
```python
@property
def server() -> uvicorn.Server | None
```

Property to access the underlying uvicorn server.



#### add_rest_endpoint[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L73)
```python
def add_rest_endpoint(address: str, method: RestMethod, endpoint: str,
                      request: type[Model] | None,
                      response: type[Model | BaseModel])
```

Add a REST endpoint to the server.



#### has_rest_endpoint[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L89)
```python
def has_rest_endpoint(method: RestMethod, endpoint: str) -> bool
```

Check if the server has a REST endpoint registered.



#### handle_readiness_probe[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L138)
```python
async def handle_readiness_probe(headers: CaseInsensitiveDict, send)
```

Handle a readiness probe sent via the HEAD method.



#### handle_missing_content_type[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L159)
```python
async def handle_missing_content_type(headers: CaseInsensitiveDict, send)
```

Handle missing content type header.



#### serve[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L171)
```python
async def serve()
```

Start the server.



#### __call__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L276)
```python
async def __call__(scope, receive, send)
```

Handle an incoming ASGI message, dispatching the envelope to the appropriate handler,
and waiting for any queries to be resolved.

