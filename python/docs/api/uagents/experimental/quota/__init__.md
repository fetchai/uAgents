

# src.uagents.experimental.quota.__init__

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



## QuotaProtocol Objects[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/quota/__init__.py#L106)

```python
class QuotaProtocol(Protocol)
```



#### __init__[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/quota/__init__.py#L107)
```python
def __init__(storage_reference: StorageAPI,
             name: str | None = None,
             version: str | None = None,
             spec: ProtocolSpecification | None = None,
             role: str | None = None,
             default_rate_limit: RateLimit | None = None,
             default_acl: AccessControlList | None = None)
```

Initialize a QuotaProtocol instance.

**Arguments**:

- `storage_reference` _StorageAPI_ - The storage reference to use for rate limiting.
- `name` _str | None_ - The name of the protocol. Defaults to None.
- `version` _str | None_ - The version of the protocol. Defaults to None.
- `spec` _ProtocolSpecification | None_ - The protocol specification. Defaults to None.
- `role` _str | None_ - The role of the protocol. Defaults to None.
- `default_rate_limit` _RateLimit | None_ - The default rate limit. Defaults to None.
- `default_acl` _AccessControlList | None_ - The access control list. Defaults to None.



#### on_message[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/quota/__init__.py#L134)
```python
def on_message(
        model: type[Model],
        replies: type[Model] | set[type[Model]] | None = None,
        allow_unverified: bool = False,
        rate_limit: RateLimit | None = None,
        access_control_list: AccessControlList | None = None) -> Callable
```

Overwritten decorator to register a message handler for the protocol
including rate limiting.

**Arguments**:

- `model` _type[Model]_ - The message model type.
- `replies` _type[Model] | set[type[Model]] | None_ - The associated reply types.
- `allow_unverified` _bool | None_ - Whether to allow unverified messages. Defaults to False.
- `rate_limit` _RateLimit | None_ - The rate limit to apply. Defaults to None.
- `access_control_list` _AccessControlList | None_ - The access control list to apply.
  

**Returns**:

- `Callable` - The decorator to register the message handler.



#### wrap[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/quota/__init__.py#L164)
```python
def wrap(func: MessageCallback,
         rate_limit: RateLimit | None = None,
         acl: AccessControlList | None = None) -> MessageCallback
```

Decorator to wrap a function with rate limiting.

**Arguments**:

- `func` _MessageCallback_ - The function to wrap.
- `rate_limit` _RateLimit | None_ - The rate limit to apply. Defaults to None.
- `acl` _AccessControlList | None_ - The access control list to apply.
  

**Returns**:

- `Callable` - The decorated



#### add_request[↗](https://github.com/fetchai/uAgents/blob/main/python/src/uagents/quota/__init__.py#L232)
```python
def add_request(agent_address: str, function_name: str,
                window_size_minutes: int, max_requests: int) -> bool
```

Add a request to the rate limiter if the current time is still within the
time window since the beginning of the most recent time window. Otherwise,
reset the time window and add the request.

**Arguments**:

- `agent_address` - The address of the agent making the request.
  

**Returns**:

  False if the maximum number of requests has been exceeded, True otherwise.

