import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Type, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import httpx
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from uagents_core.agentverse.sdk.common.av import (
    generate_agent_auth_token,
    register_to_agentverse_sync,
    send_message_to_agent,
)
from uagents_core.agentverse.sdk.common.storage import setup_agent_storage
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
from uagents_core.agentverse.sdk.langchain.config import (
    DEFAULT_ENV_VARS,
    DEFAULT_HTTP_TIMEOUT,
    DEFAULT_LANGGRAPH_ASSISTANT_ID,
    DEFAULT_LANGGRAPH_INTERNAL_BASE_URL,
    DEFAULT_LANGGRAPH_PORT,
    LangGraphAdapterConfig,
)
from uagents_core.agentverse.sdk.langchain.content import extract_ai_content
from uagents_core.agentverse.sdk.langchain.profile import _generate_registration_request
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
)
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from uagents_core.registration import AgentProfile

for ch in ["uagents_core.utils.resolver", "uagents_core.utils.messages"]:
    logging.getLogger(ch).setLevel(logging.ERROR)


@dataclass
class LangGraphAgentStarletteState(AgentStarletteState):
    assistant_id: str = ""
    chat_endpoint: str = ""


@dataclass
class LangGraphAgentContext(AgentContext):
    config: LangGraphAdapterConfig | None = None


_ctx = LangGraphAgentContext()


def bootstrap_env() -> None:
    load_dotenv()

    for key, value in DEFAULT_ENV_VARS.items():
        os.environ.setdefault(key, value)


def _resolve_url() -> str:
    return (
        os.getenv("LANGGRAPH_API_URL")
        or os.getenv("AGENT_PUBLIC_URL")
        or f"http://localhost:{os.getenv('PORT', DEFAULT_LANGGRAPH_PORT)}"
    )


def _session_to_thread_id(session: Any) -> str | None:
    if session is None:
        return None

    session_str = str(session).strip()
    if not session_str:
        return None

    try:
        return str(UUID(session_str))
    except ValueError:
        return str(uuid5(NAMESPACE_URL, f"agentverse-session:{session_str}"))


def register_to_agentverse(
    agent: AgentverseAgent,
    config: LangGraphAdapterConfig,
) -> None:

    request = _generate_registration_request(agent, config, _resolve_url())
    auth_header = {
        "Authorization": f"Agent {generate_agent_auth_token(agent.uri.identity)}"
    }

    register_to_agentverse_sync(
        request,
        auth_header,
        agent.uri.agentverse,
    )
    setup_agent_storage(_ctx, agent)


class AgentverseLangGraphApplication:
    def __init__(self, original_app: Starlette, lg_config: Any):
        self.original_app = original_app
        self.lg_config = lg_config

    def register(self) -> None:
        logger.debug("Registering with agentverse...")

        if _ctx.agent is None or _ctx.config is None:
            raise RuntimeError("Not initialised.")

        register_to_agentverse(_ctx.agent, _ctx.config)
        logger.info("Registered with agentverse")

    def _wrap_lifespan(self, existing_lifespan):
        status_lifespan = setup_agent_status_lifespan(existing_lifespan)

        @asynccontextmanager
        async def lifespan(app: Starlette):
            with handle_init_errors(_ctx.agent.uri):
                self.register()
            async with status_lifespan(app):
                yield

        return lifespan

    def build(self) -> Starlette:
        if _ctx.agent is None:
            return self.original_app

        with handle_init_errors(_ctx.agent.uri):
            original_lifespan = self.original_app.router.lifespan_context
            lifespan = self._wrap_lifespan(original_lifespan)

            app = Starlette(
                routes=[
                    Route(
                        path=_ctx.config.chat_endpoint,
                        endpoint=self._chat,
                        methods=["POST"],
                        name="Agentverse chat messages handler",
                    ),
                    Mount("", app=self.original_app),
                ],
                lifespan=lifespan,
                exception_handlers=getattr(self.original_app, "exception_handlers", {}),
            )

            app.state = self.original_app.state
            set_app_state(
                app,
                LangGraphAgentStarletteState(
                    key=_ctx.agent.uri.key,
                    agentverse=_ctx.agent.uri.agentverse,
                    assistant_id=_ctx.config.assistant_id,
                    chat_endpoint=_ctx.config.chat_endpoint,
                ),
            )

            return app

    @report_error_starlette(_ctx, "user")
    async def _chat(self, request: Request) -> Response:
        logger.debug("Received chat request")
        logger.debug("Request: %s", request)

        env, msg = await parse_chat_message_from_request(
            request, _ctx.agent.options.verify_envelope, _ctx.agent.uri.identity.address
        )
        logger.debug("Chat message from %s", env.sender)

        if isinstance(msg, ChatAcknowledgement):
            return JSONResponse({})

        return JSONResponse(
            {},
            background=BackgroundTask(
                self._process_and_reply, env=env, msg=cast(ChatMessage, msg)
            ),
        )

    @report_error(_ctx, "user")
    async def _process_and_reply(
        self,
        env: Envelope,
        msg: ChatMessage,
    ) -> None:
        logger.debug("Processing chat message from %s...", env.sender)

        sender_identity = _ctx.agent.uri.identity

        await self._send_ack(env, msg, sender_identity)

        if len(msg.content) == 1 and isinstance(msg.content[0], StartSessionContent):
            return

        text = msg.text()

        logger.debug("Processing chat message by LangGraph...")

        try:
            data = await self._call_runs_wait(text, env)
            content = await extract_ai_content(data, ctx=_ctx)
        except (json.JSONDecodeError, KeyError):
            logger.error("Malformed response from LangGraph")
            content = [
                TextContent(
                    text="Sorry, malformed response from the agent, please retry later."
                )
            ]
        except Exception as e:
            logger.error(
                "Failed to process chat message by LangGraph with error: %s", e
            )
            content = [TextContent(text="Sorry, agent failed to process request")]

        logger.debug("Chat message processed by LangGraph")

        await self._send_reply(env, content, sender_identity)
        logger.debug("Reply sent to %s", env.sender)

    def _get_runs_wait_path(self) -> str:
        if getattr(self.lg_config, "MOUNT_PREFIX", None):
            return f"{self.lg_config.MOUNT_PREFIX}/runs/wait"
        return "/runs/wait"

    def _get_thread_runs_wait_path(self, thread_id: str) -> str:
        if getattr(self.lg_config, "MOUNT_PREFIX", None):
            return f"{self.lg_config.MOUNT_PREFIX}/threads/{thread_id}/runs/wait"
        return f"/threads/{thread_id}/runs/wait"

    def _build_runs_wait_payload(
        self,
        text: str,
        env: Envelope | None = None,
    ) -> dict[str, Any]:
        config = _ctx.config

        metadata: dict[str, Any] = {}
        if env is not None:
            metadata = {
                "agentverse_sender": env.sender,
                "agentverse_target": env.target,
                "agentverse_session": str(env.session) if env.session else None,
            }
            metadata = {k: v for k, v in metadata.items() if v is not None}

        payload: dict[str, Any] = {
            "assistant_id": config.assistant_id,
            "multitask_strategy": config.multitask_strategy,
            "input": {
                "messages": [
                    {
                        "role": "human",
                        "content": text,
                    }
                ]
            },
        }

        if metadata:
            payload["metadata"] = metadata

        return payload

    async def _call_runs_wait(self, text: str, env: Envelope) -> dict[str, Any]:
        config = _ctx.config

        payload = self._build_runs_wait_payload(text, env)
        path = self._get_runs_wait_path()

        if config.use_threads:
            thread_id = _session_to_thread_id(env.session)
            if thread_id is not None:
                path = self._get_thread_runs_wait_path(thread_id)
                payload["if_not_exists"] = "create"

        transport = httpx.ASGITransport(app=self.original_app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url=DEFAULT_LANGGRAPH_INTERNAL_BASE_URL,
            timeout=DEFAULT_HTTP_TIMEOUT,
        ) as client:
            response = await client.post(path, json=payload)

        if response.status_code >= 400:
            raise RuntimeError(
                f"LangGraph call failed with {response.status_code}: {response.text}"
            )

        return response.json()

    async def _send_ack(
        self,
        env: Envelope,
        msg: ChatMessage,
        sender_identity: Identity,
    ) -> None:
        await send_message_to_agent(
            env.sender,
            ChatAcknowledgement(
                timestamp=utc_now(),
                acknowledged_msg_id=msg.msg_id,
            ),
            sender_identity,
            agentverse_config=_ctx.agent.uri.agentverse,
        )

    async def _send_reply(
        self,
        env: Envelope,
        content: list[AgentContent],
        sender_identity: Identity,
    ) -> None:
        av_response = ChatMessage(
            timestamp=utc_now(),
            msg_id=uuid4(),
            content=content or [TextContent(text="")],
        )

        await send_message_to_agent(
            env.sender,
            av_response,
            sender_identity,
            session_id=env.session,
            agentverse_config=_ctx.agent.uri.agentverse,
        )


def patch_langgraph_app(new_builder: Type[AgentverseLangGraphApplication]) -> None:
    import langgraph_api.config as lg_config
    import langgraph_api.server as lg_server

    original_app = lg_server.app
    lg_server.app = new_builder(original_app, lg_config).build()


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
        _ctx.agent = AgentverseAgent(
            uri=uri,
            profile=profile,
            metadata=metadata,
            options=AgentOptions(
                verify_envelope=(not disable_message_auth),
                enable_storage=enable_storage,
            ),
        )

        _ctx.config = LangGraphAdapterConfig()

    logger.info("Initialised agent %s", uri.name)


def run() -> None:
    if _ctx.agent is not None and _ctx.config is not None:
        bootstrap_env()

        with handle_init_errors(_ctx.agent.uri):
            patch_langgraph_app(AgentverseLangGraphApplication)

        if "--no-reload" not in sys.argv:
            sys.argv.append("--no-reload")

    logger.info("Starting LangGraph CLI...")

    from langgraph_cli.cli import cli

    cli()
