from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import AsyncGenerator, cast

from starlette import status
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from uagents_core.adapters.common.agentverse import verify_envelope
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
)
from uagents_core.envelope import Envelope
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
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unvalid envelope"
            )
        msg = cast(ChatMessage, parse_envelope(env, ChatMessage))
        return env, msg
    except HTTPException:
        raise
    except TypeError:
        try:
            msg = cast(ChatAcknowledgement, parse_envelope(env, ChatAcknowledgement))
            return env, msg
        except:
            raise malformed_exc
    except Exception as e:
        print(f"Failed to parse chat message : {str(e)}")
        raise malformed_exc


@asynccontextmanager
async def agent_status_lifespan(app: Starlette):
    await set_agent_status(app.state.agent, True)
    yield
    await set_agent_status(app.state.agent, False)


def setup_agent_status_lifespan(
    existing_lifespan: _AsyncGeneratorContextManager[None, None] | None = None,
) -> _AsyncGeneratorContextManager[None, None]:
    if existing_lifespan is None:
        return agent_status_lifespan

    async def combined_lifespan(app: Starlette):
        async with agent_status_lifespan(app):
            async with existing_lifespan(app):
                yield

    return combined_lifespan
