import importlib
import inspect
import json
import sys
from functools import wraps
from typing import Any, Type
from uuid import uuid4

import a2a
from a2a.server.apps import A2AStarletteApplication
from a2a.types import AgentCard
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from uagents_core.agentverse.sdk.common.av import (
    CHAT_PROTOCOL,
    generate_agent_auth_token,
    register_to_agentverse_sync,
    send_message_to_agent,
)
from uagents_core.agentverse.sdk.common.config import (
    DEFAULT_AGENTVERSE_CHAT_ENDPOINT,
)
from uagents_core.agentverse.sdk.common.events import (
    FAILED_INIT_ERROR_FORMAT,
    handle_init_errors,
    report_error,
)
from uagents_core.agentverse.sdk.common.helpers import utc_now
from uagents_core.agentverse.sdk.common.logger import logger
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
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
)
from uagents_core.envelope import Envelope
from uagents_core.registration import AgentProfile, RegistrationRequest
from uagents_core.types import AgentEndpoint

_ctx = AgentContext()


def _generate_readme(card: AgentCard) -> str:
    title = (
        f"{card.name} by {card.provider.organization}"
        if card.provider is not None
        else card.name
    )

    skills = []

    for skill in card.skills:
        examples = (
            "Examples\n" + "\n\n".join([f"- `{eg}`" for eg in skill.examples])
            if skill.examples is not None
            else None
        )
        skills.append(f"### {skill.name}\n{skill.description}\n\n{examples or ''}")
    skills = "\n".join(skills)

    about = (
        f"Learn more about [{card.name}]({card.documentation_url})."
        if card.documentation_url is not None
        else ""
    )
    about += (
        f"\n\nLearn more about [{card.provider.organization}]({card.provider.url})."
        if card.provider is not None
        else ""
    )
    about = f"## About\n{about}" if about else ""

    readme = f"""
# {title}
{card.description}

## What this agent can do (Skills)

{skills}


{about}
            """

    return readme


def _generate_registration_request(
    agent: AgentverseAgent, card: AgentCard | None = None
) -> RegistrationRequest:

    request = RegistrationRequest(
        address=agent.uri.identity.address,
        name=agent.uri.name,
        handle=agent.uri.handle,
        agent_type="a2a",
        profile=agent.profile or AgentProfile(),
        metadata=agent.metadata,
    )

    if card:
        request.url = card.documentation_url
        chat_url = (
            f"{card.url.strip('/')}/{DEFAULT_AGENTVERSE_CHAT_ENDPOINT.strip('/')}"
        )
        request.endpoints = [AgentEndpoint(url=chat_url, weight=1)]
        request.protocols = [CHAT_PROTOCOL]

        if not request.profile.description:
            request.profile.description = card.description
        if not request.profile.readme:
            request.profile.readme = _generate_readme(card)
        if not request.profile.avatar_url:
            request.profile.avatar_url = card.icon_url

    return request


class AgentverseA2AStarletteApplication(A2AStarletteApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registered = False

        if _ctx.agent is not None:
            with handle_init_errors(_ctx.agent.uri):
                self.register()
                self._registered = True

    def register(self):
        if _ctx.agent is None:
            raise RuntimeError("Not initialised.")

        request = _generate_registration_request(_ctx.agent, self.agent_card)
        token = generate_agent_auth_token(_ctx.agent.uri.identity)

        register_to_agentverse_sync(
            request, {"Authorization": f"Agent {token}"}, _ctx.agent.uri.agentverse
        )

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

        a2a_msg = {
            "jsonrpc": "2.0",
            "id": str(msg.msg_id),
            "method": "message/send",
            "params": {
                "message": {
                    "kind": "message",
                    "role": "user",
                    "messageId": str(uuid4()),
                    "parts": [
                        {
                            "kind": "text",
                            "text": msg.text(),
                        }
                    ],
                }
            },
        }

        async def a2a_receive():
            return {
                "type": "http.request",
                "body": json.dumps(a2a_msg).encode(),
                "more_body": False,
            }

        a2a_request = Request(
            scope=request.scope, receive=a2a_receive, send=request._send
        )
        response = ""

        try:
            resp = await super()._handle_requests(a2a_request)
            a2a_response = json.loads(resp.body)
            answer = a2a_response.get("result")
            if answer is not None:
                for part in answer["parts"]:
                    if part["kind"] != "text":
                        continue
                    response += part["text"]

        except (json.JSONDecodeError, KeyError):
            response = "Sorry, malformed response from the agent, please retry later."
        except Exception:
            response = "Sorry, agent failed to process request"

        # send the response back to the user
        av_response = ChatMessage(
            timestamp=utc_now(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response)],
        )
        await send_message_to_agent(
            destination=env.sender,
            msg=av_response,
            sender=_ctx.agent.uri.identity,
            agentverse_config=_ctx.agent.uri.agentverse,
            session_id=env.session,
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
):
    uri = None

    try:
        uri = AgentUri.from_str(agent)
    except Exception as e:
        logger.error(FAILED_INIT_ERROR_FORMAT.format(f"malformed agent URI: {str(e)}"))
        return

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
            options=AgentOptions(verify_envelope=(not disable_message_auth)),
        )
