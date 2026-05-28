import contextlib
import functools
import traceback
from contextlib import asynccontextmanager
from typing import Callable
from uuid import uuid4

from requests import HTTPError

from uagents_core.agentverse.sdk.common.av import (
    _post_data,
    _post_data_sync,
    generate_agent_auth_token,
    send_message_to_agent,
)
from uagents_core.agentverse.sdk.common.helpers import utc_now
from uagents_core.agentverse.sdk.common.logger import log_sdk, logger
from uagents_core.agentverse.sdk.common.types import (
    AgentBatchEvents,
    AgentContext,
    AgentStarletteState,
    AgentUri,
    EventCategory,
)
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent
from uagents_core.envelope import Envelope

FAILED_INIT_ERROR_FORMAT = "Failed to initialize agentverse sdk ({})"


def get_agent_address(agent: str | AgentUri) -> str | None:
    if isinstance(agent, str):
        try:
            agent = AgentUri.from_str(agent)
        except Exception:
            return None

    return agent.identity.address


def _dispatch_event_sync(
    agent: AgentUri | AgentStarletteState, events: AgentBatchEvents
):
    _post_data_sync(
        url=f"{agent.agentverse.url}/v1/events",
        data=events,
        headers={"Authorization": f"Agent {generate_agent_auth_token(agent.identity)}"},
    )


async def dispatch_event(
    agent: AgentUri | AgentStarletteState, events: AgentBatchEvents
):
    await _post_data(
        url=f"{agent.agentverse.url}/v1/events",
        data=events,
        headers={"Authorization": f"Agent {generate_agent_auth_token(agent.identity)}"},
    )


@contextlib.contextmanager
def handle_init_errors(uri: AgentUri):
    try:
        yield
    except Exception as e:
        logger.error("Init error suppressed: %s", e)
        event = AgentBatchEvents.from_exception(e, traceback.format_exc())
        try:
            _dispatch_event_sync(uri, event)
        except HTTPError as dispatch_exception:
            log_sdk(
                FAILED_INIT_ERROR_FORMAT.format(
                    f"{dispatch_exception.response.status_code} at {utc_now().timestamp()}"
                )
            )
        except Exception as generic_exception:
            log_sdk(FAILED_INIT_ERROR_FORMAT.format(str(generic_exception)))


def report_error(
    ctx: AgentContext, category: EventCategory = "user", reraise: bool = False
):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error("Error reported: %s", e)
                event = AgentBatchEvents.from_exception(
                    e, traceback.format_exc(), category
                )
                if ctx.agent is not None:
                    await dispatch_event_safe(ctx.agent.uri, event)
                if reraise:
                    raise e

        return wrapper

    return decorator


class ChatProcessingError(Exception):
    """Raised inside @report_error_reply functions to control error handling behavior."""

    def __init__(
        self,
        message: str,
        category: EventCategory = "system",
        exc: Exception | None = None,
    ):
        self.reply_text = message
        self.category = category
        self.exc = exc
        super().__init__(message)


DEFAULT_ERROR_REPLY = "Agent failed to process request, please retry later."


async def dispatch_event_safe(
    agent: AgentUri | AgentStarletteState, event: AgentBatchEvents
):
    """Dispatch event to Agentverse. Swallows failures."""
    try:
        await dispatch_event(agent, event)
    except Exception as e:
        logger.error("Failed to dispatch event: %s", e)


@asynccontextmanager
async def chat_error_on_fail(
    message: str,
    category: EventCategory = "system",
    include_exc: bool = True,
):
    """Wraps an operation. On failure, raises ChatProcessingError."""
    try:
        yield
    except Exception as e:
        raise ChatProcessingError(
            message,
            category=category,
            exc=e if include_exc or category == "system" else None,
        ) from e


def report_error_reply(ctx: AgentContext, category: EventCategory = "system"):
    """Decorator: on exception, dispatch event + send error reply."""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, env: Envelope, *args, **kwargs):
            try:
                return await func(self, env, *args, **kwargs)
            except ChatProcessingError as e:
                if e.exc:
                    tb = "".join(traceback.format_exception(e.exc))
                    await dispatch_event_safe(
                        ctx.agent.uri,
                        AgentBatchEvents.from_exception(e.exc, tb, e.category),
                    )
                else:
                    await dispatch_event_safe(
                        ctx.agent.uri,
                        AgentBatchEvents.from_message(
                            e.reply_text, e.category, "error"
                        ),
                    )
                await _send_error_reply(ctx, env, e.reply_text)
            except Exception as e:
                await dispatch_event_safe(
                    ctx.agent.uri,
                    AgentBatchEvents.from_exception(
                        e, traceback.format_exc(), category
                    ),
                )
                await _send_error_reply(ctx, env, DEFAULT_ERROR_REPLY)

        return wrapper

    return decorator


async def _send_error_reply(ctx: AgentContext, env: Envelope, text: str):
    """Last-resort error reply. Self-guarded — never raises."""
    if ctx.agent is None:
        return
    try:
        await send_message_to_agent(
            destination=env.sender,
            msg=ChatMessage(
                timestamp=utc_now(),
                msg_id=uuid4(),
                content=[TextContent(text=text)],
            ),
            sender=ctx.agent.uri.identity,
            agentverse_config=ctx.agent.uri.agentverse,
            session_id=env.session,
        )
    except Exception as e:
        logger.error("Failed to send error reply to %s: %s", env.sender, e)
        await dispatch_event_safe(
            ctx.agent.uri,
            AgentBatchEvents.from_message(
                f"Failed to deliver error reply to {env.sender}: {e}",
                "user",
                "info",
            ),
        )
