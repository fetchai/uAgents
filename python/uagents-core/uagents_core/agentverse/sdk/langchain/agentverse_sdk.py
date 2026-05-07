import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Type, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from uagents_core.agentverse.sdk.common.av import (
    CHAT_PROTOCOL,
    generate_agent_auth_token,
    register_to_agentverse_sync,
    send_message_to_agent,
)
from uagents_core.agentverse.sdk.common.config import DEFAULT_AGENTVERSE_CHAT_ENDPOINT
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
)
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
)
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from uagents_core.registration import AgentProfile, RegistrationRequest
from uagents_core.types import AgentEndpoint

for ch in ["uagents_core.utils.resolver", "uagents_core.utils.messages"]:
    logging.getLogger(ch).setLevel(logging.ERROR)


@dataclass
class LangGraphAgentStarletteState(AgentStarletteState):
    assistant_id: str = ""
    chat_endpoint: str = ""


class LangGraphAdapterConfig(BaseModel):
    assistant_id: str = DEFAULT_LANGGRAPH_ASSISTANT_ID
    chat_endpoint: str = DEFAULT_AGENTVERSE_CHAT_ENDPOINT
    use_threads: bool = True
    multitask_strategy: str = "enqueue"


@dataclass
class LangGraphAgentContext(AgentContext):
    config: LangGraphAdapterConfig | None = None


_ctx = LangGraphAgentContext()


def bootstrap_env() -> None:
    load_dotenv()

    for key, value in DEFAULT_ENV_VARS.items():
        os.environ.setdefault(key, value)


def _combine_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _resolve_public_url() -> str | None:
    return os.getenv("LANGGRAPH_API_URL")


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


def _generate_readme(
    agent: AgentverseAgent,
    config: LangGraphAdapterConfig,
    public_url: str,
) -> str:
    chat_url = _combine_url(public_url, config.chat_endpoint)

    return f"""# {agent.uri.name}
LangGraph agent bridged to Agentverse.

## What this agent can do
- Receive Agentverse chat messages at `{config.chat_endpoint}`
- Forward incoming text to LangGraph assistant `{config.assistant_id}`
- Return the model response back through the Agentverse chat protocol

## Endpoints
- Base URL: {public_url}
- Chat endpoint: {chat_url}
"""


def _generate_registration_request(
    agent: AgentverseAgent,
    config: LangGraphAdapterConfig,
    public_url: str,
) -> RegistrationRequest:
    identity = agent.uri.identity

    profile_data = agent.profile.model_dump() if agent.profile is not None else {}
    profile = AgentProfile(**profile_data)

    if not profile.description:
        profile.description = (
            f"LangGraph agent '{config.assistant_id}' bridged to Agentverse."
        )

    if not profile.readme:
        profile.readme = _generate_readme(agent, config, public_url)

    request = RegistrationRequest(
        address=identity.address,
        name=agent.uri.name,
        handle=agent.uri.handle,
        agent_type="uagent",
        profile=profile,
        metadata=agent.metadata,
    )

    request.url = public_url
    request.endpoints = [
        AgentEndpoint(
            url=_combine_url(public_url, config.chat_endpoint),
            weight=1,
        )
    ]
    request.protocols = [CHAT_PROTOCOL]

    return request


def register_to_agentverse(
    agent: AgentverseAgent,
    config: LangGraphAdapterConfig,
) -> None:
    public_url = _resolve_public_url()
    if public_url is None:
        raise RuntimeError("Could not resolve public URL for registration.")

    request = _generate_registration_request(agent, config, public_url)
    auth_header = {
        "Authorization": f"Agent {generate_agent_auth_token(agent.uri.identity)}"
    }

    register_to_agentverse_sync(
        request,
        auth_header,
        agent.uri.agentverse,
    )


class AgentverseLangGraphApplication:
    def __init__(self, original_app: Starlette, lg_config: Any):
        self.original_app = original_app
        self.lg_config = lg_config
        self._registered = False

        if _ctx.agent is not None:
            with handle_init_errors(_ctx.agent.uri):
                self.register()
                self._registered = True

    def register(self) -> None:
        logger.debug("Registering with agentverse...")

        if _ctx.agent is None or _ctx.config is None:
            raise RuntimeError("Not initialised.")

        register_to_agentverse(_ctx.agent, _ctx.config)
        logger.info("Registered with agentverse")

    def build(self) -> Starlette:
        if _ctx.agent is None or not self._registered:
            return self.original_app

        with handle_init_errors(_ctx.agent.uri):
            original_lifespan = self.original_app.router.lifespan_context
            lifespan = setup_agent_status_lifespan(original_lifespan)

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
            response_text = self._extract_last_ai_text(data)
        except (json.JSONDecodeError, KeyError):
            logger.error("Malformed response from LangGraph")
            response_text = (
                "Sorry, malformed response from the agent, please retry later."
            )
        except Exception as e:
            logger.error(
                "Failed to process chat message by LangGraph with error: %s", e
            )
            response_text = "Sorry, agent failed to process request"

        logger.debug("Chat message processed by LangGraph")

        await self._send_reply(env, response_text, sender_identity)
        logger.debug("Reply sent to %s", env.sender)

    def _get_runs_wait_path(self) -> str:
        if getattr(self.lg_config, "MOUNT_PREFIX", None):
            return f"{self.lg_config.MOUNT_PREFIX}/runs/wait"
        return "/runs/wait"

    def _get_thread_runs_wait_path(self, thread_id: str) -> str:
        if getattr(self.lg_config, "MOUNT_PREFIX", None):
            return f"{self.lg_config.MOUNT_PREFIX}/threads/{thread_id}/runs/wait"
        return f"/threads/{thread_id}/runs/wait"

    def _extract_last_ai_text(self, data: dict[str, Any]) -> str:
        messages = data.get("messages")
        if not isinstance(messages, list):
            values = data.get("values", {})
            messages = values.get("messages", []) if isinstance(values, dict) else []

        for msg in reversed(messages):
            msg_type = msg.get("type")
            msg_role = msg.get("role")
            if msg_type not in {"ai", "assistant"} and msg_role != "assistant":
                continue

            content = msg.get("content", "")

            if isinstance(content, str):
                return content

            if isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            parts.append(text)
                return "\n".join(parts)

        return ""

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
        response_text: str,
        sender_identity: Identity,
    ) -> None:
        av_response = ChatMessage(
            timestamp=utc_now(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response_text)],
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
            options=AgentOptions(verify_envelope=(not disable_message_auth)),
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
