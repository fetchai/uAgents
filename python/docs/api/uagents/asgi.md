<a id="src.uagents.asgi"></a>

# src.uagents.asgi

<a id="src.uagents.asgi.ASGIServer"></a>

## ASGIServer Objects

```python
class ASGIServer()
```

ASGI server for receiving incoming envelopes.

<a id="src.uagents.asgi.ASGIServer.__init__"></a>

#### `__`init`__`

```python
def __init__(port: int,
             loop: asyncio.AbstractEventLoop,
             queries: Dict[str, asyncio.Future],
             logger: Optional[Logger] = None)
```

Initialize the ASGI server.

**Arguments**:

- `port` _int_ - The port to listen on.
- `loop` _asyncio.AbstractEventLoop_ - The event loop to use.
- `queries` _Dict[str, asyncio.Future]_ - The dictionary of queries to resolve.
- `logger` _Optional[Logger]_ - The logger to use.

<a id="src.uagents.asgi.ASGIServer.server"></a>

#### server

```python
@property
def server()
```

Property to access the underlying uvicorn server.

Returns: The server.

<a id="src.uagents.asgi.ASGIServer.add_rest_endpoint"></a>

#### add`_`rest`_`endpoint

```python
def add_rest_endpoint(address: str, method: RestMethod, endpoint: str,
                      request: Optional[Type[Model]],
                      response: Type[Union[Model, BaseModel]])
```

Add a REST endpoint to the server.

<a id="src.uagents.asgi.ASGIServer.has_rest_endpoint"></a>

#### has`_`rest`_`endpoint

```python
def has_rest_endpoint(method: RestMethod, endpoint: str) -> bool
```

Check if the server has a REST endpoint registered.

<a id="src.uagents.asgi.ASGIServer.handle_readiness_probe"></a>

#### handle`_`readiness`_`probe

```python
async def handle_readiness_probe(headers: CaseInsensitiveDict, send)
```

Handle a readiness probe sent via the HEAD method.

<a id="src.uagents.asgi.ASGIServer.handle_missing_content_type"></a>

#### handle`_`missing`_`content`_`type

```python
async def handle_missing_content_type(headers: CaseInsensitiveDict, send)
```

Handle missing content type header.

<a id="src.uagents.asgi.ASGIServer.serve"></a>

#### serve

```python
async def serve()
```

Start the server.

<a id="src.uagents.asgi.ASGIServer.__call__"></a>

#### `__`call`__`

```python
async def __call__(scope, receive, send)
```

Handle an incoming ASGI message, dispatching the envelope to the appropriate handler,
and waiting for any queries to be resolved.

