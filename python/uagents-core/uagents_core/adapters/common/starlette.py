from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import cast

from starlette import status
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from uagents_core.adapters.common.agentverse import verify_envelope
from uagents_core.adapters.common.types import AgentStarletteState
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
)
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from uagents_core.utils.messages import parse_envelope
from uagents_core.adapters.common.agentverse import set_agent_status


async def parse_chat_message_from_request(
    request: Request, verify: bool
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
        msg = cast(
            ChatMessage | ChatAcknowledgement | str,
            parse_envelope(env, {ChatMessage, ChatAcknowledgement}),
        )
        if isinstance(msg, str):
            raise malformed_exc

        return env, msg
    except Exception as e:
        print(f"Failed to parse chat message : {str(e)}")
        raise malformed_exc


@asynccontextmanager
async def agent_status_lifespan(app: Starlette):
    await set_agent_status(app.state.agent.identity, True, app.state.agent.agentverse)
    yield
    await set_agent_status(app.state.agent.identity, False, app.state.agent.agentverse)


def setup_agent_status_lifespan(
    existing_lifespan: _AsyncGeneratorContextManager[None, None] | None = None,
) -> _AsyncGeneratorContextManager[None, None]:
    if existing_lifespan is None:
        return agent_status_lifespan

    @asynccontextmanager
    async def combined_lifespan(app: Starlette):
        async with agent_status_lifespan(app):
            async with existing_lifespan(app):
                yield

    return combined_lifespan


def set_app_state(app: Starlette, agent: AgentStarletteState):
    app.state.agent = agent
