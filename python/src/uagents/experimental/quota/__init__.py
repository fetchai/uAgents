"""
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

"""

import functools
import time
from collections.abc import Callable

from pydantic import BaseModel
from uagents_core.models import ErrorMessage

from uagents import Context, Model, Protocol
from uagents.storage import StorageAPI
from uagents.types import MessageCallback

WINDOW_SIZE_MINUTES = 60
MAX_REQUESTS = 6


class Usage(BaseModel):
    time_window_start: float
    window_size_minutes: int
    requests: int
    max_requests: int


class RateLimit(BaseModel):
    window_size_minutes: int
    max_requests: int


class AccessControlList(BaseModel):
    default: bool
    allowed: set[str] = set()
    blocked: set[str] = set()
    bypass_rate_limit: set[str] = set()


class QuotaProtocol(Protocol):
    def __init__(
        self,
        storage_reference: StorageAPI,
        name: str | None = None,
        version: str | None = None,
        default_rate_limit: RateLimit | None = None,
        default_acl: AccessControlList | None = None,
    ):
        """
        Initialize a QuotaProtocol instance.

        Args:
            storage_reference (StorageAPI): The storage reference to use for rate limiting.
            name (str | None): The name of the protocol. Defaults to None.
            version (str | None): The version of the protocol. Defaults to None.
            default_rate_limit (RateLimit | None): The default rate limit. Defaults to None.
            default_acl (AccessControlList | None): The access control list. Defaults to None.
        """
        super().__init__(name=name, version=version)
        self.storage_ref = storage_reference
        self.default_rate_limit = default_rate_limit
        self.default_acl = default_acl

    def on_message(
        self,
        model: type[Model],
        replies: type[Model] | set[type[Model]] | None = None,
        allow_unverified: bool = False,
        rate_limit: RateLimit | None = None,
        access_control_list: AccessControlList | None = None,
    ) -> Callable:
        """
        Overwritten decorator to register a message handler for the protocol
        including rate limiting.

        Args:
            model (type[Model]): The message model type.
            replies (type[Model] | set[type[Model]] | None): The associated reply types.
            allow_unverified (bool | None): Whether to allow unverified messages. Defaults to False.
            rate_limit (RateLimit | None): The rate limit to apply. Defaults to None.
            access_control_list (AccessControlList | None): The access control list to apply.

        Returns:
            Callable: The decorator to register the message handler.
        """

        def decorator_on_message(func: MessageCallback):
            handler = self.wrap(func, rate_limit, access_control_list)
            self._add_message_handler(model, handler, replies, allow_unverified)
            return handler

        return decorator_on_message

    def wrap(
        self,
        func: MessageCallback,
        rate_limit: RateLimit | None = None,
        acl: AccessControlList | None = None,
    ) -> MessageCallback:
        """
        Decorator to wrap a function with rate limiting.

        Args:
            func (MessageCallback): The function to wrap.
            rate_limit (RateLimit | None): The rate limit to apply. Defaults to None.
            acl (AccessControlList | None): The access control list to apply.

        Returns:
            Callable: The decorated
        """
        acl = acl or self.default_acl
        if acl is None:
            acl = AccessControlList(default=True)

        rate_limit = rate_limit or self.default_rate_limit

        @functools.wraps(func)
        async def decorator(ctx: Context, sender: str, msg: type[Model]):
            if (acl.default and sender in acl.blocked) or (
                not acl.default and sender not in acl.allowed
            ):
                return await ctx.send(
                    sender,
                    ErrorMessage(error=("You are not allowed to access this handler.")),
                )
            if (
                sender in acl.bypass_rate_limit
                or not rate_limit
                or self.add_request(
                    agent_address=sender,
                    function_name=func.__name__,
                    window_size_minutes=rate_limit.window_size_minutes,
                    max_requests=rate_limit.max_requests,
                )
            ):
                result = await func(ctx, sender, msg)
            else:
                err = (
                    f"Rate limit exceeded for {msg.schema()['title']}. "
                    f"This handler allows for {rate_limit.max_requests} calls per "
                    f"{rate_limit.window_size_minutes} minutes. Try again later."
                )
                result = await ctx.send(sender, ErrorMessage(error=err))
            return result

        return decorator  # type: ignore

    def _clean_usage(self, usage: dict[str, dict]) -> None:
        """
        Remove all time windows that are older than the current time window.

        Args:
            usage: The usage dictionary to clean
        """
        now = int(time.time())
        for key in list(usage.keys()):
            if (now - usage[key]["time_window_start"]) > usage[key][
                "window_size_minutes"
            ] * 60:
                del usage[key]

    def add_request(
        self,
        agent_address: str,
        function_name: str,
        window_size_minutes: int,
        max_requests: int,
    ) -> bool:
        """
        Add a request to the rate limiter if the current time is still within the
        time window since the beginning of the most recent time window. Otherwise,
        reset the time window and add the request.

        Args:
            agent_address: The address of the agent making the request.

        Returns:
            False if the maximum number of requests has been exceeded, True otherwise.
        """
        now = int(time.time())

        usage = self.storage_ref.get(agent_address) or {}

        if function_name in usage:
            quota = Usage(**usage[function_name])
            if (now - quota.time_window_start) <= window_size_minutes * 60:
                if quota.requests >= max_requests:
                    return False
                quota.requests += 1
            else:
                quota.time_window_start = now
                quota.requests = 1
            usage[function_name] = quota.model_dump()
        else:
            usage[function_name] = Usage(
                time_window_start=now,
                window_size_minutes=window_size_minutes,
                requests=1,
                max_requests=max_requests,
            ).model_dump()

        self._clean_usage(usage)

        self.storage_ref.set(agent_address, usage)

        return True
