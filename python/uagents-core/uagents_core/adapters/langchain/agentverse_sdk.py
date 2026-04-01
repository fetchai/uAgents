import asyncio
import ipaddress
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from secrets import token_bytes
from typing import Any, Tuple, Type, cast
from urllib.parse import unquote, urlparse
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel
from starlette import status
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from uagents_core.config import AgentverseConfig
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity, is_user_address
from uagents_core.protocol import ProtocolSpecification
from uagents_core.registration import AgentProfile, RegistrationRequest
from uagents_core.storage import compute_attestation
from uagents_core.types import AgentEndpoint
from uagents_core.utils.messages import parse_envelope, send_message_to_agent
from uagents_core.utils.registration import (
    AgentverseRequestError,
    _send_post_request_agentverse,
)

DEFAULT_AGENTVERSE_CHAT_ENDPOINT = "/av/chat"
DEFAULT_HTTP_REQUESTS_TIMEOUT = 3
DEFAULT_LANGGRAPH_INTERNAL_BASE_URL = "http://langgraph.internal"
DEFAULT_LANGGRAPH_ASSISTANT_ID = "agent"
DEFAULT_HTTP_TIMEOUT = 60.0
AGENT_AUTH_TOKEN_VALIDITY = 60 * 2

for ch in ["uagents_core.utils.resolver", "uagents_core.utils.messages"]:
    logging.getLogger(ch).setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


class AgentUri(BaseModel):
    key: str
    name: str
    agentverse_config: AgentverseConfig
    handle: str | None = None

    @classmethod
    def from_str(cls, uri: str) -> "AgentUri":
        parsed = urlparse(uri)

        if not parsed.scheme:
            raise ValueError("Scheme is missing.")
        if not parsed.hostname:
            raise ValueError("Hostname is missing.")
        if not parsed.username:
            raise ValueError("Agent handle is missing.")
        if not parsed.password:
            raise ValueError("Agent key is missing.")
        if not parsed.path or len(parsed.path.split("/")) < 2:
            raise ValueError("Agent name is missing.")

        name = unquote(parsed.path.split("/")[1])

        agentverse = AgentverseConfig(
            base_url=parsed.hostname + (f":{parsed.port}" if parsed.port else ""),
            http_prefix=parsed.scheme,
        )

        return cls(
            key=parsed.password,
            name=name,
            agentverse_config=agentverse,
            handle=parsed.username,
        )


class AgentverseAgent(BaseModel):
    uri: AgentUri
    profile: AgentProfile | None = None
    metadata: dict[str, Any] | None = None
    verify_envelope: bool


class LangGraphAdapterConfig(BaseModel):
    assistant_id: str = DEFAULT_LANGGRAPH_ASSISTANT_ID
    chat_endpoint: str = DEFAULT_AGENTVERSE_CHAT_ENDPOINT
    debug_http_response: bool = False
    register_on_startup: bool = True


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


def generate_agent_auth_token(identity: Identity) -> str:
    return compute_attestation(
        identity,
        datetime.now(timezone.utc),
        AGENT_AUTH_TOKEN_VALIDITY,
        token_bytes(32),
    )


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
    identity = Identity.from_seed(agent.uri.key, 0)

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
    request.protocols = [
        ProtocolSpecification.compute_digest(chat_protocol_spec.manifest())
    ]

    return request


def _register_to_agentverse(
    request: RegistrationRequest,
    headers: dict[str, str],
    agentverse: AgentverseConfig,
    timeout: int = DEFAULT_HTTP_REQUESTS_TIMEOUT,
) -> None:
    try:
        _send_post_request_agentverse(
            url=agentverse.agents_api,
            data=request,
            headers=headers,
            timeout=timeout,
        )
    except AgentverseRequestError:
        raise
    except Exception:
        raise


def register_to_agentverse(
    agent: AgentverseAgent,
    config: LangGraphAdapterConfig,
) -> None:
    public_url = _resolve_public_url()
    if public_url is None:
        raise RuntimeError("Could not resolve public URL for registration.")

    identity = Identity.from_seed(agent.uri.key, 0)
    request = _generate_registration_request(agent, config, public_url)
    auth_header = {
        "Authorization": f"Agent {generate_agent_auth_token(identity)}"
    }

    _register_to_agentverse(
        request=request,
        headers=auth_header,
        agentverse=agent.uri.agentverse_config,
    )


def verify_envelope(envelope: Envelope) -> bool:
    try:
        if is_user_address(envelope.sender):
            return True
        return envelope.verify()
    except Exception:
        return False


async def _parse_chat_request(
    request: Request,
    verify: bool,
) -> Tuple[Envelope, ChatMessage | ChatAcknowledgement]:
    malformed_exc = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Malformed envelope or chat message",
    )

    try:
        env = Envelope.model_validate(await request.json())
        if verify and not verify_envelope(env):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid envelope",
            )
        msg = cast(ChatMessage, parse_envelope(env, ChatMessage))
        return env, msg
    except HTTPException:
        raise
    except TypeError:
        try:
            msg = cast(ChatAcknowledgement, parse_envelope(env, ChatAcknowledgement))
            return env, msg
        except Exception:
            raise malformed_exc
    except Exception as e:
        logger.exception("Failed to parse chat message: %s", str(e))
        raise malformed_exc


class AgentverseLangGraphApplication:
    def __init__(self, original_app: Starlette, lg_config: Any):
        self.original_app = original_app
        self.lg_config = lg_config

    def _get_runs_wait_path(self) -> str:
        if getattr(self.lg_config, "MOUNT_PREFIX", None):
            return f"{self.lg_config.MOUNT_PREFIX}/runs/wait"
        return "/runs/wait"

    def _extract_last_ai_text(self, data: dict[str, Any]) -> str:
        messages = data.get("messages", [])

        for msg in reversed(messages):
            if msg.get("type") != "ai":
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

    def _extract_text_content(self, msg: ChatMessage) -> str:
        return msg.text()

    def _build_runs_wait_payload(self, text: str) -> dict[str, Any]:
        if _config is None:
            raise RuntimeError("Adapter not initialised.")

        return {
            "assistant_id": _config.assistant_id,
            "input": {
                "messages": [
                    {
                        "role": "human",
                        "content": text,
                    }
                ]
            },
        }

    async def _call_runs_wait(self, text: str) -> dict[str, Any]:
        payload = self._build_runs_wait_payload(text)

        transport = httpx.ASGITransport(app=self.original_app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url=DEFAULT_LANGGRAPH_INTERNAL_BASE_URL,
            timeout=DEFAULT_HTTP_TIMEOUT,
        ) as client:
            response = await client.post(self._get_runs_wait_path(), json=payload)

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
        if _agent is None:
            raise RuntimeError("Adapter not initialised.")

        await asyncio.to_thread(
            send_message_to_agent,
            destination=env.sender,
            msg=ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=msg.msg_id,
            ),
            sender=sender_identity,
            agentverse_config=_agent.uri.agentverse_config,
        )

    async def _send_reply(
        self,
        env: Envelope,
        response_text: str,
        sender_identity: Identity,
    ) -> None:
        if _agent is None:
            raise RuntimeError("Adapter not initialised.")

        av_response = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response_text)],
        )

        await asyncio.to_thread(
            send_message_to_agent,
            destination=env.sender,
            msg=av_response,
            sender=sender_identity,
            agentverse_config=_agent.uri.agentverse_config,
            session_id=env.session,
        )

    async def _chat(self, request: Request) -> Response:
        if _agent is None or _config is None:
            return JSONResponse({"error": "Adapter not initialised."}, status_code=500)

        logger.info("Received request on %s", _config.chat_endpoint)

        try:
            env, msg = await _parse_chat_request(request, _agent.verify_envelope)
        except HTTPException as e:
            logger.error("Failed to parse incoming chat request: %s", e.detail)
            return JSONResponse({"detail": e.detail}, status_code=e.status_code)

        logger.info("Received envelope from %s to %s", env.sender, env.target)

        if isinstance(msg, ChatAcknowledgement):
            logger.info("Received ChatAcknowledgement")
            return JSONResponse({})

        sender_identity = Identity.from_seed(_agent.uri.key, 0)

        if len(msg.content) == 1 and isinstance(msg.content[0], StartSessionContent):
            await self._send_ack(env, msg, sender_identity)
            return JSONResponse({})

        text = self._extract_text_content(msg)
        logger.info("Received ChatMessage text: %s", text)

        if _config.debug_http_response:
            try:
                data = await self._call_runs_wait(text)
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

            body: dict[str, Any] = {"response": response_text, "raw": data}
            return JSONResponse(body)

        try:
            await self._send_ack(env, msg, sender_identity)
        except Exception as e:
            logger.exception("Failed to send acknowledgement: %s", str(e))
            return JSONResponse(
                {"error": "failed to send acknowledgement", "detail": str(e)},
                status_code=502,
            )

        if not text.strip():
            response_text = "I did not receive any text content."
        else:
            try:
                data = await self._call_runs_wait(text)
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
            return JSONResponse(
                {"error": "failed to send reply", "detail": str(e)},
                status_code=502,
            )

        return JSONResponse({})

    def register(self) -> None:
        global _registered

        if _agent is None or _config is None:
            raise RuntimeError("Not initialised.")

        public_url = _resolve_public_url()
        if not _is_publicly_reachable_url(public_url):
            logger.info(
                "Skipping Agentverse registration because the resolved URL is not public: %r",
                public_url,
            )
            return

        register_to_agentverse(_agent, _config)
        _registered = True

        logger.info(
            "Registered LangGraph agent '%s' with endpoint %s",
            _agent.uri.name,
            _combine_url(public_url, _config.chat_endpoint),
        )

    def build(self) -> Starlette:
        if _agent is None or _config is None:
            raise RuntimeError("Not initialised.")

        original_lifespan = self.original_app.router.lifespan_context

        @asynccontextmanager
        async def wrapped_lifespan(app: Starlette):
            async with original_lifespan(self.original_app):
                global _registered

                if _config.register_on_startup and not _registered:
                    try:
                        self.register()
                    except AgentverseRequestError as e:
                        raise RuntimeError(
                            f"Failed to register agent in Agentverse: {e}"
                        ) from e

                yield

        app = Starlette(
            routes=[
                Route(_config.chat_endpoint, self._chat, methods=["POST"]),
                Mount("", app=self.original_app),
            ],
            lifespan=wrapped_lifespan,
            exception_handlers=getattr(self.original_app, "exception_handlers", {}),
        )

        app.state = self.original_app.state
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
        verify_envelope=(not disable_message_auth),
    )

    _config = LangGraphAdapterConfig()


def run() -> None:
    if _agent is None or _config is None:
        raise RuntimeError("Adapter not initialised. Call init(...) first.")

    bootstrap_env()
    patch_langgraph_app(AgentverseLangGraphApplication)

    from langgraph_cli.cli import cli

    if "--no-reload" not in sys.argv:
        sys.argv.append("--no-reload")

    cli()