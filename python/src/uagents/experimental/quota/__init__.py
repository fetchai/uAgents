"""
This Protocol class can be used to rate limit `on_message` message handlers.

The rate limiter uses the agents storage to keep track of the number of requests
made by another agent within a given time window. If the number of requests exceeds
a specified limit, the rate limiter will block further requests until the time
window resets.

> Default: 6 requests per hour

Additionally, the protocol can be used to set access control rules for handlers
allowing or blocking specific agents from accessing the handler.
The default access control rule can be set to allow or block all agents.

Both rules can work together to provide a secure and rate-limited environment for
message handlers.


Usage examples:

```python
from uagents.experimental.quota import AccessControlList, QuotaProtocol, RateLimit

quota_protocol = QuotaProtocol(
    storage_reference=agent.storage,
    name="quota_proto",
    version=agent._version,
)  # Initialize the QuotaProtocol instance

# This message handler is rate limited with default values
@quota_protocol.on_message(ExampleMessage1)
async def handle(ctx: Context, sender: str, msg: ExampleMessage1):
    ...

# This message handler is rate limited with custom window size and request limit
@agent.on_message(ExampleMessage2, rate_limit=RateLimit(window_size_minutes=1, max_requests=3))
async def handle(ctx: Context, sender: str, msg: ExampleMessage2):
    ...

# This message handler has access control rules set
@agent.on_message(ExampleMessage2, acl=AccessControlList(default=False, allowed={"agent1"}))
async def handle(ctx: Context, sender: str, msg: ExampleMessage2):
    ...

agent.include(quota_protocol)
```

Tip: The `AccessControlList` object can be used to set access control rules during
runtime. This can be useful for dynamic access control rules based on the state of the
agent or the network.
```python
acl = AccessControlList(default=True, allowed={""}, blocked={""})

@proto.on_message(model=Message, access_control_list=acl)
async def message_handler(ctx: Context, sender: str, msg: Message):
    if REASON_TO_BLOCK:
        acl.blocked.add(sender)
    ctx.logger.info(f"Received message from {sender}: {msg.text}")
```

"""

import functools
import time
from typing import Optional, Set, Type, Union

from pydantic import BaseModel

from uagents import Context, Model, Protocol
from uagents.models import ErrorMessage
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
    allowed: set[str]
    blocked: set[str]


class QuotaProtocol(Protocol):
    def __init__(
        self,
        storage_reference: StorageAPI,
        name: Optional[str] = None,
        version: Optional[str] = None,
        default_rate_limit: Optional[RateLimit] = None,
    ):
        """
        Initialize a QuotaProtocol instance.

        Args:
            storage_reference (StorageAPI): The storage reference to use for rate limiting.
            name (Optional[str], optional): The name of the protocol. Defaults to None.
            version (Optional[str], optional): The version of the protocol. Defaults to None.
            acl (Optional[AccessControlList], optional): The access control list. Defaults to None.
        """
        super().__init__(name=name, version=version)
        self.storage_ref = storage_reference
        self.default_rate_limit = default_rate_limit or RateLimit(
            window_size_minutes=WINDOW_SIZE_MINUTES, max_requests=MAX_REQUESTS
        )

    def on_message(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        allow_unverified: Optional[bool] = False,
        rate_limit: Optional[RateLimit] = None,
        access_control_list: Optional[AccessControlList] = None,
    ):
        """
        Overwritten decorator to register a message handler for the protocol
        including rate limiting.

        Args:
            model (Type[Model]): The message model type.
            replies (Optional[Union[Type[Model], Set[Type[Model]]]], optional): The associated
            reply types. Defaults to None.
            allow_unverified (Optional[bool], optional): Whether to allow unverified messages.
            Defaults to False.
            window_size_minutes (int, optional): The size of the time window in minutes.
            max_requests (int, optional): The maximum number of requests allowed in the time window.

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
        rate_limit: Optional[RateLimit] = None,
        acl: Optional[AccessControlList] = None,
    ) -> MessageCallback:
        """
        Decorator to wrap a function with rate limiting.

        Args:
            func: The function to wrap with rate limiting
            window_size_minutes: The size of the time window in minutes
            max_requests: The maximum number of requests allowed in the time window

        Returns:
            Callable: The decorated
        """
        if acl is None:
            acl = AccessControlList(default=True, allowed=set(), blocked=set())

        @functools.wraps(func)
        async def decorator(ctx: Context, sender: str, msg: Type[Model]):
            if (acl.default and sender in acl.blocked) or (
                not acl.default and sender not in acl.allowed
            ):
                return await ctx.send(
                    sender,
                    ErrorMessage(
                        error=("You are not allowed to access this endpoint.")
                    ),
                )
            if not rate_limit or self.add_request(
                sender,
                func.__name__,
                rate_limit.window_size_minutes,
                rate_limit.max_requests,
            ):
                result = await func(ctx, sender, msg)
            else:
                result = await ctx.send(
                    sender,
                    ErrorMessage(
                        error=(
                            f"Rate limit exceeded for {msg.schema()["title"]}. "
                            f"This endpoint allows for {rate_limit.max_requests} calls per "
                            f"{rate_limit. window_size_minutes} minutes. Try again later."
                        )
                    ),
                )
            return result

        return decorator  # type: ignore

    def _clean_usage(self, usage: dict[str, dict]):
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
            agent_address: The address of the agent making the request

        Returns:
            False if the maximum number of requests has been exceeded, True otherwise
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
