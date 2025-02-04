<a id="src.uagents.experimental.quota.__init__"></a>

# src.uagents.experimental.quota.`__`init`__`

This Protocol class can be used to rate limit `on_message` message handlers.

The rate limiter uses the agents storage to keep track of the number of requests
made by another agent within a given time window. If the number of requests exceeds
a specified limit, the rate limiter will block further requests until the time
window resets.

> Default: Not rate limited, but you can set a default during initialization.

Additionally, the protocol can be used to set access control rules for handlers
allowing or blocking specific agents from accessing the handler.
The default access control rule can be set to allow or block all agents.

Both rules can work together to provide a secure and rate-limited environment for
message handlers.


Usage examples:

```python
from uagents.experimental.quota import AccessControlList, QuotaProtocol, RateLimit

# Initialize the QuotaProtocol instance
quota_protocol = QuotaProtocol(
    storage_reference=agent.storage,
    name="quota_proto",
    version=agent._version,
    # default_rate_limit=RateLimit(window_size_minutes=1, max_requests=3), # Optional
)

# This message handler is not rate limited
@quota_protocol.on_message(ExampleMessage1)
async def handle(ctx: Context, sender: str, msg: ExampleMessage1):
    ...

# This message handler is rate limited with custom window size and request limit
@quota_protocol.on_message(
    ExampleMessage2,
    rate_limit=RateLimit(window_size_minutes=1, max_requests=3),
)
async def handle(ctx: Context, sender: str, msg: ExampleMessage2):
    ...

# This message handler has access control rules set
@quota_protocol.on_message(
    ExampleMessage3,
    acl=AccessControlList(default=False, allowed={"<agent_address>"}),
)
async def handle(ctx: Context, sender: str, msg: ExampleMessage3):
    ...

agent.include(quota_protocol)
```

Tip: The `AccessControlList` object can be used to set access control rules during
runtime. This can be useful for dynamic access control rules based on the state of the
agent or the network.
```python
acl = AccessControlList(default=True)

@proto.on_message(model=Message, access_control_list=acl)
async def message_handler(ctx: Context, sender: str, msg: Message):
    if REASON_TO_BLOCK:
        acl.blocked.add(sender)
    ctx.logger.info(f"Received message from {sender}: {msg.text}")
```

<a id="src.uagents.experimental.quota.__init__.QuotaProtocol"></a>

## QuotaProtocol Objects

```python
class QuotaProtocol(Protocol)
```

<a id="src.uagents.experimental.quota.__init__.QuotaProtocol.__init__"></a>

#### `__`init`__`

```python
def __init__(storage_reference: StorageAPI,
             name: Optional[str] = None,
             version: Optional[str] = None,
             default_rate_limit: Optional[RateLimit] = None,
             default_acl: Optional[AccessControlList] = None)
```

Initialize a QuotaProtocol instance.

**Arguments**:

- `storage_reference` _StorageAPI_ - The storage reference to use for rate limiting.
- `name` _Optional[str], optional_ - The name of the protocol. Defaults to None.
- `version` _Optional[str], optional_ - The version of the protocol. Defaults to None.
- `default_rate_limit` _Optional[RateLimit], optional_ - The default rate limit.
  Defaults to None.
- `default_acl` _Optional[AccessControlList], optional_ - The access control list.
  Defaults to None.

<a id="src.uagents.experimental.quota.__init__.QuotaProtocol.on_message"></a>

#### on`_`message

```python
def on_message(model: Type[Model],
               replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
               allow_unverified: Optional[bool] = False,
               rate_limit: Optional[RateLimit] = None,
               access_control_list: Optional[AccessControlList] = None)
```

Overwritten decorator to register a message handler for the protocol
including rate limiting.

**Arguments**:

- `model` _Type[Model]_ - The message model type.
- `replies` _Optional[Union[Type[Model], Set[Type[Model]]]], optional_ - The associated
  reply types. Defaults to None.
- `allow_unverified` _Optional[bool], optional_ - Whether to allow unverified messages.
  Defaults to False.
- `rate_limit` _Optional[RateLimit], optional_ - The rate limit to apply. Defaults to None.
- `access_control_list` _Optional[AccessControlList], optional_ - The access control list to
  apply.
  

**Returns**:

- `Callable` - The decorator to register the message handler.

<a id="src.uagents.experimental.quota.__init__.QuotaProtocol.wrap"></a>

#### wrap

```python
def wrap(func: MessageCallback,
         rate_limit: Optional[RateLimit] = None,
         acl: Optional[AccessControlList] = None) -> MessageCallback
```

Decorator to wrap a function with rate limiting.

**Arguments**:

- `func` - The function to wrap with rate limiting
- `rate_limit` - The rate limit to apply
- `acl` - The access control list to apply
  

**Returns**:

- `Callable` - The decorated

<a id="src.uagents.experimental.quota.__init__.QuotaProtocol.add_request"></a>

#### add`_`request

```python
def add_request(agent_address: str, function_name: str,
                window_size_minutes: int, max_requests: int) -> bool
```

Add a request to the rate limiter if the current time is still within the
time window since the beginning of the most recent time window. Otherwise,
reset the time window and add the request.

**Arguments**:

- `agent_address` - The address of the agent making the request
  

**Returns**:

  False if the maximum number of requests has been exceeded, True otherwise

