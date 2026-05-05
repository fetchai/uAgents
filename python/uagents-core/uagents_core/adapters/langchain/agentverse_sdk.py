import asyncio
import ipaddress
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Type, cast
from urllib.parse import urlparse
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from uagents_core.adapters.common.agentverse import (
    CHAT_PROTOCOL,
    generate_agent_auth_token,
    register_to_agentverse_sync,
    send_message_to_agent,
)
from uagents_core.adapters.common.config import DEFAULT_AGENTVERSE_CHAT_ENDPOINT
from uagents_core.adapters.common.starlette import parse_chat_message_from_request
from uagents_core.adapters.common.types import (
    AgentOptions,
    AgentStarletteState,
    AgentUri,
    AgentverseAgent,
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
from uagents_core.utils.registration import AgentverseRequestError

DEFAULT_LANGGRAPH_INTERNAL_BASE_URL = "http://langgraph.internal"
DEFAULT_LANGGRAPH_ASSISTANT_ID = "agent"
DEFAULT_HTTP_TIMEOUT = 60.0

for ch in ["uagents_core.utils.resolver", "uagents_core.utils.messages"]:
    logging.getLogger(ch).setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


class LangGraphAgentStarletteState(AgentStarletteState):
    assistant_id: str
    chat_endpoint: str


class LangGraphAdapterConfig(BaseModel):
    assistant_id: str = DEFAULT_LANGGRAPH_ASSISTANT_ID
    chat_endpoint: str = DEFAULT_AGENTVERSE_CHAT_ENDPOINT
    debug_http_response: bool = False
    register_on_startup: bool = True
    use_threads: bool = True
    multitask_strategy: str = "enqueue"


_agent: AgentverseAgent | None = None
_config: LangGraphAdapterConfig | None = None
_registered = False


def bootstrap_env() -> None:
    load_dotenv()

    os.environ.setdefault("LANGGRAPH_RUNTIME_EDITION", "inmem")
    os.environ.setdefault(
        "DATABASE_URI",
        "postgresql://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable",
    )
    os.environ.setdefault("REDIS_URI", "redis://127.0.0.1:6379/0")


def _require_agent() -> AgentverseAgent:
    if _agent is None:
        raise RuntimeError("Adapter not initialised. Call init(...) first.")
    return _agent


def _require_config() -> LangGraphAdapterConfig:
    if _config is None:
        raise RuntimeError("Adapter not initialised. Call init(...) first.")
    return _config


def _get_sender_identity() -> Identity:
    return _require_agent().uri.identity


def _combine_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _resolve_public_url() -> str | None:
    return os.getenv("LANGGRAPH_API_URL")


def _is_publicly_reachable_url(url: str | None) -> bool:
    if not url:
        return False

    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return False

        if host in {"localhost", "0.0.0.0"}:
            return False

        try:
            ip = ipaddress.ip_address(host)
            if ip.is_loopback or ip.is_private or ip.is_link_local:
                return False
        except ValueError:
            pass

        return True
    except Exception:
        return False


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


def _set_app_state(app: Starlette) -> None:
    config = _require_config()
    agent = _require_agent()

    app.state.agent = LangGraphAgentStarletteState(
        key=agent.uri.key,
        agentverse=agent.uri.agentverse,
        assistant_id=config.assistant_id,
        chat_endpoint=config.chat_endpoint,
    )


class AgentverseLangGraphApplication:
    def __init__(self, original_app: Starlette, lg_config: Any):
        self.original_app = original_app
        self.lg_config = lg_config

    def _get_runs_wait_path(self) -> str:
        if getattr(self.lg_config, "MOUNT_PREFIX", None):
            return f"{self.lg_config.MOUNT_PREFIX}/runs/wait"
        return "/runs/wait"

    def _get_thread_runs_wait_path(self, thread_id: str) -> str:
        if getattr(self.lg_config, "MOUNT_PREFIX", None):
            return f"{self.lg_config.MOUNT_PREFIX}/threads/{thread_id}/runs/wait"
        return f"/threads/{thread_id}/runs/wait"

    def _extract_text_content(self, msg: ChatMessage) -> str:
        return msg.text()

    def _extract_last_ai_text(self, data: dict[str, Any]) -> str:
        messages = data.get("messages")
        if not isinstance(messages, list):
            values = data.get("values", {})
            if isinstance(values, dict):
                messages = values.get("messages", [])
            else:
                messages = []

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
        config = _require_config()

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
        config = _require_config()

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
        agent = _require_agent()

        await send_message_to_agent(
            env.sender,
            ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=msg.msg_id,
            ),
            sender_identity,
            agentverse_config=agent.uri.agentverse,
        )

    async def _send_reply(
        self,
        env: Envelope,
        response_text: str,
        sender_identity: Identity,
    ) -> None:
        agent = _require_agent()

        av_response = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response_text)],
        )

        await send_message_to_agent(
            env.sender,
            av_response,
            sender_identity,
            session_id=env.session,
            agentverse_config=agent.uri.agentverse,
        )

    async def _process_and_reply(
        self,
        env: Envelope,
        text: str,
        sender_identity: Identity,
    ) -> None:
        if not text.strip():
            response_text = "I did not receive any text content."
        else:
            try:
                data = await self._call_runs_wait(text, env)
                response_text = self._extract_last_ai_text(data)
                if not response_text:
                    response_text = "Sorry, I received an empty response."
            except Exception as e:
                logger.exception(
                    "Failed to process request by LangGraph agent: %s", str(e)
                )
                response_text = "Sorry, agent is not reachable."

        try:
            await self._send_reply(env, response_text, sender_identity)
        except Exception as e:
            logger.exception("Failed to send reply: %s", str(e))

    async def _chat(self, request: Request) -> Response:
        agent = _require_agent()
        config = _require_config()

        logger.info("Received request on %s", config.chat_endpoint)

        try:
            env, msg = await parse_chat_message_from_request(
                request, agent.options.verify_envelope
            )
        except HTTPException as e:
            logger.error("Failed to parse incoming chat request: %s", e.detail)
            return JSONResponse({"detail": e.detail}, status_code=e.status_code)

        logger.info("Received envelope from %s to %s", env.sender, env.target)

        if isinstance(msg, ChatAcknowledgement):
            logger.info("Received ChatAcknowledgement")
            return JSONResponse({})

        sender_identity = _get_sender_identity()

        if len(msg.content) == 1 and isinstance(msg.content[0], StartSessionContent):
            await self._send_ack(env, cast(ChatMessage, msg), sender_identity)
            return JSONResponse({})

        text = self._extract_text_content(cast(ChatMessage, msg))
        logger.info("Received ChatMessage text: %s", text)

        if config.debug_http_response:
            try:
                data = await self._call_runs_wait(text, env)
                response_text = (
                    self._extract_last_ai_text(data)
                    or "Sorry, I received an empty response."
                )
            except Exception as e:
                logger.exception(
                    "Failed to process request by LangGraph agent: %s", str(e)
                )
                return JSONResponse(
                    {"error": "langgraph call failed", "detail": str(e)},
                    status_code=502,
                )

            return JSONResponse({"response": response_text, "raw": data})

        try:
            await self._send_ack(env, cast(ChatMessage, msg), sender_identity)
        except Exception as e:
            logger.exception("Failed to send acknowledgement: %s", str(e))
            return JSONResponse(
                {"error": "failed to send acknowledgement", "detail": str(e)},
                status_code=502,
            )

        asyncio.create_task(self._process_and_reply(env, text, sender_identity))
        return JSONResponse({})

    def register(self) -> None:
        global _registered

        agent = _require_agent()
        config = _require_config()

        public_url = _resolve_public_url()
        if not _is_publicly_reachable_url(public_url):
            logger.info(
                "Skipping Agentverse registration because the resolved URL is not public: %r",
                public_url,
            )
            return

        register_to_agentverse(agent, config)
        _registered = True

        logger.info(
            "Registered LangGraph agent '%s' with endpoint %s",
            agent.uri.name,
            _combine_url(public_url, config.chat_endpoint),
        )

    def build(self) -> Starlette:
        _require_agent()
        config = _require_config()

        original_lifespan = self.original_app.router.lifespan_context

        @asynccontextmanager
        async def wrapped_lifespan(app: Starlette):
            async with original_lifespan(self.original_app):
                global _registered

                if config.register_on_startup and not _registered:
                    try:
                        self.register()
                    except AgentverseRequestError as e:
                        raise RuntimeError(
                            f"Failed to register agent in Agentverse: {e}"
                        ) from e

                yield

        app = Starlette(
            routes=[
                Route(
                    path=config.chat_endpoint,
                    endpoint=self._chat,
                    methods=["POST"],
                    name="Agentverse chat messages handler",
                ),
                Mount("", app=self.original_app),
            ],
            lifespan=wrapped_lifespan,
            exception_handlers=getattr(self.original_app, "exception_handlers", {}),
        )

        app.state = self.original_app.state
        _set_app_state(app)
        return app


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
) -> None:
    global _agent, _config, _registered
    _registered = False

    _agent = AgentverseAgent(
        uri=AgentUri.from_str(agent),
        profile=profile,
        metadata=metadata,
        options=AgentOptions(verify_envelope=(not disable_message_auth)),
    )

    _config = LangGraphAdapterConfig()


def run() -> None:
    _require_agent()
    _require_config()

    bootstrap_env()
    patch_langgraph_app(AgentverseLangGraphApplication)

    from langgraph_cli.cli import cli

    if "--no-reload" not in sys.argv:
        sys.argv.append("--no-reload")

    cli()
