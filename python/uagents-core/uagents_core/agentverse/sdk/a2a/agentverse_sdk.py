import importlib
import inspect
import sys
from functools import wraps
from typing import Any, Type
from uuid import uuid4

import a2a
from a2a.server.apps import A2AStarletteApplication
from a2a.types import Message as A2AMessage
from a2a.types import (
    MessageSendParams,
    Part,
    TextPart,
)
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from uagents_core.agentverse.sdk.a2a.content import extract_content, is_task_complete
from uagents_core.agentverse.sdk.a2a.profile import _generate_registration_request
from uagents_core.agentverse.sdk.common.av import (
    generate_agent_auth_token,
    register_to_agentverse_sync,
    send_message_to_agent,
)
from uagents_core.agentverse.sdk.common.storage import setup_agent_storage
from uagents_core.agentverse.sdk.common.config import (
    DEFAULT_AGENTVERSE_CHAT_ENDPOINT,
)
from uagents_core.agentverse.sdk.common.events import (
    FAILED_INIT_ERROR_FORMAT,
    handle_init_errors,
    report_error,
)
from uagents_core.agentverse.sdk.common.helpers import utc_now
from uagents_core.agentverse.sdk.common.logger import configure, log_sdk, logger
from uagents_core.agentverse.sdk.common.starlette import (
    parse_chat_message_from_request,
    report_error_starlette,
    set_app_state,
    setup_agent_status_lifespan,
)
from uagents_core.agentverse.sdk.common.types import (
    AgentContext,
    AgentOptions,
    AgentStarletteState,
    AgentUri,
    AgentverseAgent,
)
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
)
from uagents_core.envelope import Envelope
from uagents_core.registration import AgentProfile, RegistrationRequest
from uagents_core.types import AgentEndpoint

_ctx = AgentContext()


class AgentverseA2AStarletteApplication(A2AStarletteApplication):
    def __init__(self, agent_card, http_handler, **kwargs):
        self._request_handler = http_handler
        self._session_contexts: dict[str, str] = {}
        super().__init__(agent_card, http_handler, **kwargs)
        self._registered = False

        if _ctx.agent is not None:
            with handle_init_errors(_ctx.agent.uri):
                self.register()
                self._registered = True

    def register(self):
        logger.debug("Registering with agentverse...")

        if _ctx.agent is None:
            raise RuntimeError("Not initialised.")

        request = _generate_registration_request(_ctx.agent, self.agent_card)
        token = generate_agent_auth_token(_ctx.agent.uri.identity)

        register_to_agentverse_sync(
            request, {"Authorization": f"Agent {token}"}, _ctx.agent.uri.agentverse
        )

        if _ctx.agent is not None:
            setup_agent_storage(_ctx, _ctx.agent)

        logger.info("Registered with agentverse")

    @wraps(A2AStarletteApplication.build)
    def build(self, *args, **kwargs) -> Starlette:

        if _ctx.agent is not None and self._registered:
            with handle_init_errors(_ctx.agent.uri):
                kwargs["lifespan"] = setup_agent_status_lifespan(kwargs.get("lifespan"))

        app = super().build(*args, **kwargs)

        if _ctx.agent is not None and self._registered:
            with handle_init_errors(_ctx.agent.uri):
                app.add_route(
                    name="Agentverse chat messages handler",
                    path=DEFAULT_AGENTVERSE_CHAT_ENDPOINT,
                    methods=["POST"],
                    route=self._chat,
                )

                set_app_state(
                    app,
                    AgentStarletteState(
                        key=_ctx.agent.uri.key,
                        agentverse=_ctx.agent.uri.agentverse,
                    ),
                )

        return app

    @report_error_starlette(_ctx, "user")
    async def _chat(self, request: Request) -> Response:
        agent = _ctx.agent
        env, msg = await parse_chat_message_from_request(
            request, agent.options.verify_envelope, agent.uri.identity.address
        )
        logger.debug("Chat message from %s", env.sender)

        if isinstance(msg, ChatAcknowledgement):
            return JSONResponse({})

        return JSONResponse(
            {},
            background=BackgroundTask(
                self._process_chat_message_bg, request=request, env=env, msg=msg
            ),
        )

    @report_error(_ctx, "user")
    async def _process_chat_message_bg(
        self, request: Request, env: Envelope, msg: ChatMessage
    ):
        logger.debug("Processing chat message from %s...", env.sender)

        agent = _ctx.agent
        await send_message_to_agent(
            destination=env.sender,
            msg=ChatAcknowledgement(
                timestamp=utc_now(), acknowledged_msg_id=msg.msg_id
            ),
            sender=agent.uri.identity,
            agentverse_config=agent.uri.agentverse,
        )

        if len(msg.content) == 1 and isinstance(msg.content[0], StartSessionContent):
            return

        context_id = self._session_contexts.get(env.session)
        params = MessageSendParams(
            message=A2AMessage(
                role="user",
                message_id=str(uuid4()),
                context_id=context_id,
                parts=[Part(root=TextPart(text=msg.text()))],
            ),
        )

        logger.debug("Processing chat message by a2a server...")

        try:
            async for event in self._request_handler.on_message_send_stream(params):
                if is_task_complete(event):
                    self._session_contexts.pop(env.session, None)
                else:
                    self._session_contexts[env.session] = event.context_id

                content = await extract_content(event, ctx=_ctx)
                if content:
                    await self._send_reply(
                        content=content,
                        destination=env.sender,
                        session_id=env.session,
                    )
        except Exception as e:
            logger.error("A2A agent error: %s", e)
            await self._send_reply(
                content=[
                    TextContent(
                        type="text",
                        text="Agent failed to process request, please retry later.",
                    )
                ],
                destination=env.sender,
                session_id=env.session,
            )
            raise

        logger.debug("Chat message processed by a2a server")

    async def _send_reply(
        self,
        content: list[AgentContent],
        destination: str,
        session_id: str | None = None,
    ):
        agent = _ctx.agent
        await send_message_to_agent(
            destination=destination,
            msg=ChatMessage(
                timestamp=utc_now(),
                msg_id=uuid4(),
                content=content,
            ),
            sender=agent.uri.identity,
            agentverse_config=agent.uri.agentverse,
            session_id=session_id,
        )


def patch_a2a_app_builder(new_builder: Type):
    importlib.reload(a2a)
    a2a.server.apps.A2AStarletteApplication = new_builder
    sys.modules["a2a"] = a2a


def init(
    agent: str,
    *,
    profile: AgentProfile | None = None,
    metadata: dict[str, Any] | None = None,
    disable_message_auth: bool = False,
    enable_storage: bool = False,
):
    uri = None

    logger.debug("Initialising agent %s...", agent)

    try:
        uri = AgentUri.from_str(agent)
    except Exception as e:
        log_sdk(FAILED_INIT_ERROR_FORMAT.format(f"malformed agent URI: {e}"))
        return

    if uri.log_level is not None:
        configure(uri.log_level)

    with handle_init_errors(uri):
        # instrument a2a starlette
        patch_a2a_app_builder(AgentverseA2AStarletteApplication)
        gl = inspect.stack()[1].frame.f_globals
        gl["A2AStarletteApplication"] = AgentverseA2AStarletteApplication

        # store the agent info
        _ctx.agent = AgentverseAgent(
            uri=uri,
            profile=profile,
            metadata=metadata,
            options=AgentOptions(
                verify_envelope=(not disable_message_auth),
                enable_storage=enable_storage,
            ),
        )

    logger.info("Initialised agent %s", uri.name)
