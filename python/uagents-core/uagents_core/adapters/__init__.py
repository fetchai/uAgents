import os
import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional, cast
from pydantic.v1 import ValidationError

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from uagents_core.contrib.protocols.chat import ChatAcknowledgement, ChatMessage, TextContent
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from uagents_core.utils.messages import parse_envelope, send_message_to_agent
from uagents_core.utils.registration import (
    register_chat_agent,
    RegistrationRequestCredentials,
)


AGENT_SEED_PHRASE_ENV = "AGENT_SEED_PHRASE"
AGENTVERSE_API_KEY_ENV = "AGENTVERSE_API_KEY"


MsgCallback = Callable[[str], Coroutine[Any, Any, Optional[str]]]


class ChatProtocolMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        msg_callback: MsgCallback,
        msg_route: str = "/chat",
        agent_seed_phrase: Optional[str] = None,
    ) -> None:
        super().__init__(app)
        self.msg_callback = msg_callback
        self.msg_route = msg_route

        seed = agent_seed_phrase or os.environ.get(AGENT_SEED_PHRASE_ENV)
        if not seed:
            raise RuntimeError(
                f"{self.__class__.__name__}: no seed phrase provided. "
                f"Set {AGENT_SEED_PHRASE_ENV} or pass `agent_seed_phrase=`."
            )
        self._identity = Identity.from_seed(seed, 0)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == self.msg_route and request.method.upper() == "POST":
            try:
                body = await request.json()
                env = Envelope.model_validate(body)

                payload_str = env.decode_payload()
                payload_obj = json.loads(payload_str) if payload_str else {}

            except Exception as exc:
                return JSONResponse(
                    {"error": f"Invalid envelope or payload: {exc}"},
                    status_code=400,
                )

            if isinstance(payload_obj, dict) and "acknowledged_msg_id" in payload_obj:
                print(
                    f"Received ChatAcknowledgement from {env.sender} "
                    f"for {payload_obj.get('acknowledged_msg_id')}"
                )
                return JSONResponse({"status": "ack-ignored"}, status_code=200)

            try:
                msg = ChatMessage.parse_obj(payload_obj)
            except (ValidationError, TypeError) as exc:
                return JSONResponse(
                    {"error": f"Invalid ChatMessage payload: {exc}"},
                    status_code=400,
                )


            acknowledge_msg = ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=msg.msg_id,
            )

            send_message_to_agent(
                destination=env.sender,
                msg=acknowledge_msg,
                sender=self._identity,
            )

            text = msg.text()
            reply_text = await self.msg_callback(text)

            if reply_text:
                reply_msg = ChatMessage([TextContent(reply_text)])

                send_message_to_agent(
                    destination=env.sender,
                    msg=reply_msg,
                    sender=self._identity,
                )

            return JSONResponse({"status": "accepted"}, status_code=200)

        return await call_next(request)


def attach_and_register_adapter(
    app: FastAPI,
    agent_name: str,
    public_endpoint: str,
    msg_callback: MsgCallback,
    msg_route: str = "/chat",
    agent_seed_phrase: Optional[str] = None,
    agentverse_api_key: Optional[str] = None,
    active: bool = True,
) -> None:

    seed = agent_seed_phrase or os.environ.get(AGENT_SEED_PHRASE_ENV)
    if not seed:
        raise RuntimeError(
            "attach_chat_protocol_adapter: no seed phrase provided. "
            f"Set {AGENT_SEED_PHRASE_ENV} or pass `agent_seed_phrase=`."
        )

    api_key = agentverse_api_key or os.environ.get(AGENTVERSE_API_KEY_ENV)

    base = public_endpoint.rstrip("/")
    route = msg_route if msg_route.startswith("/") else "/" + msg_route
    full_endpoint = base + route 

    if not api_key:
        raise RuntimeError(
            "attach_chat_protocol_adapter: no Agentverse API key provided. "
            f"Set {AGENTVERSE_API_KEY_ENV} or pass `agentverse_api_key=`."
        )

    register_chat_agent(
        agent_name,
        full_endpoint,
        active=active,
        credentials=RegistrationRequestCredentials(
            agentverse_api_key=api_key,
            agent_seed_phrase=seed,
        ),
    )

    app.add_middleware(
        ChatProtocolMiddleware,
        msg_callback=msg_callback,
        msg_route=route,
        agent_seed_phrase=seed,
    )
