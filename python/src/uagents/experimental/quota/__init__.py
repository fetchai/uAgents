"""
This agent class can be used to rate limit your message handlers.

The rate limiter uses the agents storage to keep track of the number of requests
made by another agent within a given time window. If the number of requests exceeds
a specified limit, the rate limiter will block further requests until the time
window resets.

> Default: 6 requests per hour

Usage examples:

This message handler is rate limited with default values:
```python
@agent.on_message(ExampleMessage)
async def handle(ctx: Context, sender: str, msg: ExampleMessage):
    ...
```

This message handler is rate limited with custom window size and request limit:
```python
@agent.on_message(ExampleMessage, window_size_minutes=30, max_requests=10)
async def handle(ctx: Context, sender: str, msg: ExampleMessage):
    ...
```

Also applies to protocol message handlers if you import the QuotaProtocol class:
```python
protocol = QuotaProtocol(
    quota_callback=agent.add_request,
    name="quota_proto",
    version=agent._version,
)

@protocol.on_message(ExampleMessage)
async def handle(ctx: Context, sender: str, msg: ExampleMessage):
    ...

agent.include(protocol)
```
"""

import functools
import time
from typing import Callable, Optional, Set, Type, Union

from pydantic import BaseModel

from uagents import Agent, Context, Model, Protocol
from uagents.models import ErrorMessage
from uagents.types import MessageCallback

WINDOW_SIZE_MINUTES = 60
MAX_REQUESTS = 6


class Usage(BaseModel):
    time_window_start: float
    window_size_minutes: int
    requests: int
    max_requests: int


class QuotaProtocol(Protocol):
    def __init__(self, quota_callback: Callable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quota_callback = quota_callback

    def on_message(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        allow_unverified: Optional[bool] = False,
        window_size_minutes: int = WINDOW_SIZE_MINUTES,
        max_requests: int = MAX_REQUESTS,
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
            handler = self.wrap(func, window_size_minutes, max_requests)
            self._add_message_handler(model, handler, replies, allow_unverified)
            return handler

        return decorator_on_message

    def wrap(
        self,
        func: MessageCallback,
        window_size_minutes: int = WINDOW_SIZE_MINUTES,
        max_requests: int = MAX_REQUESTS,
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

        @functools.wraps(func)
        async def decorator(ctx: Context, sender: str, msg: Type[Model]):
            if self.quota_callback(
                sender, func.__name__, window_size_minutes, max_requests
            ):
                result = await func(ctx, sender, msg)
            else:
                result = await ctx.send(
                    sender,
                    ErrorMessage(
                        error=(
                            f"Rate limit exceeded for {msg.schema()["title"]}. "
                            f"This endpoint allows for {max_requests} calls per "
                            f"{window_size_minutes} minutes. Try again later."
                        )
                    ),
                )
            return result

        return decorator  # type: ignore


class QuotaAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._protocol = QuotaProtocol(
            quota_callback=self.add_request, name=self._name, version=self._version
        )

        # only necessary because this feature is not implemented in the core
        @self.on_message(ErrorMessage)
        async def _handle_error_message(ctx: Context, sender: str, msg: ErrorMessage):
            ctx.logger.exception(f"Received error message from {sender}: {msg.error}")

    def on_message(
        self,
        model: Type[Model],
        replies: Optional[Union[Type[Model], Set[Type[Model]]]] = None,
        allow_unverified: Optional[bool] = False,
        window_size_minutes: int = WINDOW_SIZE_MINUTES,
        max_requests: int = MAX_REQUESTS,
    ):
        """
        Overwritten decorator to register an message handler for the provided
        message model including rate limiting.

        Args:
            model (Type[Model]): The message model.
            replies (Optional[Union[Type[Model], Set[Type[Model]]]]): Optional reply models.
            allow_unverified (Optional[bool]): Allow unverified messages.
            window_size_minutes (int): The size of the time window in minutes.
            max_requests (int): The maximum number of requests allowed in the time window.

        Returns:
            Callable: The decorator function for registering message handlers.

        """

        return self._protocol.on_message(
            model, replies, allow_unverified, window_size_minutes, max_requests
        )

    def _add_error_message_handler(self):
        # This would not be necessary if this feature was implemented in the core
        pass

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

        usage = self.storage.get(agent_address) or {}

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

        self.storage.set(agent_address, usage)

        return True
