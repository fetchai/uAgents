import functools
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Callable, cast

from starlette import status
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request

from uagents_core.agentverse.sdk.common.av import set_agent_status, verify_envelope
from uagents_core.agentverse.sdk.common.events import dispatch_event, report_error
from uagents_core.agentverse.sdk.common.logger import logger
from uagents_core.agentverse.sdk.common.types import (
    AgentBatchEvents,
    AgentContext,
    AgentStarletteState,
    EventCategory,
)
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
)
from uagents_core.envelope import Envelope
from uagents_core.utils.messages import parse_envelope


async def parse_chat_message_from_request(
    request: Request, verify: bool, expected_address: str | None = None
) -> tuple[Envelope, ChatMessage | ChatAcknowledgement]:
    malformed_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Malformed envelope or chat message",
    )

    try:
        env = Envelope.model_validate(await request.json())
        if verify and not verify_envelope(env):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid envelope"
            )
        if expected_address is not None and env.target != expected_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wrong destination address",
            )
        msg = cast(
            ChatMessage | ChatAcknowledgement | str,
            parse_envelope(env, {ChatMessage, ChatAcknowledgement}),
        )
        if isinstance(msg, str):
            raise malformed_exc

        return env, msg
    except Exception as e:
        raise malformed_exc from e


@asynccontextmanager
async def agent_status_lifespan(app: Starlette):
    if hasattr(app.state, "agent"):
        agent = app.state.agent
        try:
            await set_agent_status(agent.identity, True, agent.agentverse)
            await dispatch_event(
                agent, AgentBatchEvents.from_message("Agent Started")
            )
        except Exception as e:
            logger.error("Failed to report agent start: %s", e)
    yield
    if hasattr(app.state, "agent"):
        agent = app.state.agent
        try:
            await set_agent_status(agent.identity, False, agent.agentverse)
            await dispatch_event(
                agent, AgentBatchEvents.from_message("Agent Stopped")
            )
        except Exception as e:
            logger.error("Failed to report agent stop: %s", e)


Lifespan = Callable[[Starlette], AbstractAsyncContextManager[None]]


def setup_agent_status_lifespan(
    existing_lifespan: Lifespan | None = None,
) -> Lifespan:
    if existing_lifespan is None:
        return agent_status_lifespan

    @asynccontextmanager
    async def combined_lifespan(app: Starlette):
        async with agent_status_lifespan(app), existing_lifespan(app):
            yield

    return combined_lifespan


def set_app_state(app: Starlette, agent: AgentStarletteState):
    app.state.agent = agent


def report_error_starlette(ctx: AgentContext, category: EventCategory = "user"):
    def decorator(func: Callable):
        reported = report_error(ctx, category, reraise=True)(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await reported(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process request",
                ) from e

        return wrapper

    return decorator
