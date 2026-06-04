import os
import json
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional
from pydantic.v1 import ValidationError

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from uagents_core.contrib.protocols.chat import ChatAcknowledgement, ChatMessage, TextContent
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from uagents_core.utils.messages import send_message_to_agent


AGENT_SEED_PHRASE = os.getenv("AGENT_SEED_PHRASE")
if not AGENT_SEED_PHRASE:
    raise RuntimeError(
        "AGENT_SEED_PHRASE env var is required to use ChatProtocolMiddleware."
    )


MsgCallback = Callable[[str], Coroutine[Any, Any, Optional[str]]]


class ChatProtocolMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        msg_callback: MsgCallback,
        msg_route: str = "/chat",
    ) -> None:
        super().__init__(app)
        self.msg_callback = msg_callback
        self.msg_route = msg_route
        self._identity = Identity.from_seed(AGENT_SEED_PHRASE, 0)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == self.msg_route and request.method.upper() == "POST":
            try:
                body = await request.json()
                env = Envelope.model_validate(body)
            except Exception as exc:
                return JSONResponse(
                    {"error": f"Invalid envelope: {exc}"},
                    status_code=400,
                )

            try:
                payload_str = env.decode_payload()
                payload_obj = json.loads(payload_str) if payload_str else {}
            except Exception as exc:
                error_message = f"Invalid payload: {exc}"
                reply_msg = ChatMessage([TextContent(error_message)])

                send_message_to_agent(
                    destination=env.sender,
                    msg=reply_msg,
                    sender=self._identity,
                )
                return JSONResponse(
                    {"error": error_message},
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
                error_message = f"Invalid ChatMessage payload: {exc}"
                reply_msg = ChatMessage([TextContent(error_message)])

                send_message_to_agent(
                    destination=env.sender,
                    msg=reply_msg,
                    sender=self._identity,
                )
                return JSONResponse(
                    {"error": error_message},
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


def attach_adapter(
    app: FastAPI,
    msg_callback: MsgCallback,
    msg_route: str = "/chat",
) -> None:

    app.add_middleware(
        ChatProtocolMiddleware,
        msg_callback=msg_callback,
        msg_route=msg_route,
    )
