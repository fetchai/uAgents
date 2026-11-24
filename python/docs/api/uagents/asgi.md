

# src.uagents.asgi



## RequestBodyTooLargeError Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L34)

```python
class RequestBodyTooLargeError(Exception)
```

Raised when an incoming request body exceeds the maximum allowed size.



## ASGIServer Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L63)

```python
class ASGIServer()
```

ASGI server for receiving incoming envelopes.



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L66)
```python
def __init__(port: int,
             loop: asyncio.AbstractEventLoop,
             queries: dict[tuple[str, UUID], asyncio.Future],
             logger: Logger | None = None,
             max_body_size: int | None = None)
```

Initialize the ASGI server.

**Arguments**:

- `port` _int_ - The port to listen on.
- `loop` _asyncio.AbstractEventLoop_ - The event loop to use.
- `queries` _dict[tuple[str, UUID], asyncio.Future]_ - The dictionary of pending
  sync queries to resolve, keyed by (sender, session).
- `logger` _Logger | None_ - The logger to use.
- `max_body_size` _int | None_ - The maximum size of an incoming request body
  in bytes; larger requests are rejected with a 413 response. If None,
  DEFAULT_MAX_BODY_SIZE_BYTES is used.



#### server[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L99)
```python
@property
def server() -> uvicorn.Server | None
```

Property to access the underlying uvicorn server.



#### add_rest_endpoint[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L104)
```python
def add_rest_endpoint(address: str, method: RestMethod, endpoint: str,
                      request: type[Model] | None,
                      response: type[Model | BaseModel])
```

Add a REST endpoint to the server.



#### has_rest_endpoint[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L120)
```python
def has_rest_endpoint(method: RestMethod, endpoint: str) -> bool
```

Check if the server has a REST endpoint registered.



#### handle_readiness_probe[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L169)
```python
async def handle_readiness_probe(headers: CaseInsensitiveDict, send)
```

Handle a readiness probe sent via the HEAD method.



#### handle_missing_content_type[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L195)
```python
async def handle_missing_content_type(headers: CaseInsensitiveDict, send)
```

Handle missing content type header.



#### serve[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L207)
```python
async def serve()
```

Start the server.



#### __call__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/asgi.py#L320)
```python
async def __call__(scope, receive, send)
```

Handle an incoming ASGI message, dispatching the envelope to the appropriate handler,
and waiting for any queries to be resolved.

