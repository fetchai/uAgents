import importlib
import inspect
import json
import sys
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Type
from uuid import uuid4

import a2a
from a2a.server.apps import A2AStarletteApplication
from a2a.types import AgentCard
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from uagents_core.adapters.common.agentverse import (
    _register_to_agentverse,
    generate_agent_auth_token,
)
from uagents_core.adapters.common.config import (
    DEFAULT_AGENTVERSE_CHAT_ENDPOINT,
)
from uagents_core.adapters.common.starlette import _parse_chat_request
from uagents_core.adapters.common.types import AgentUri, AgentverseAgent
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.identity import Identity
from uagents_core.protocol import ProtocolSpecification
from uagents_core.registration import AgentProfile, RegistrationRequest
from uagents_core.types import AgentEndpoint
from uagents_core.utils.messages import send_message_to_agent

_agent: AgentverseAgent | None = None


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
    identity = Identity.from_seed(agent.uri.key, 0)

    request = RegistrationRequest(
        address=identity.address,
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
        request.protocols = [
            ProtocolSpecification.compute_digest(chat_protocol_spec.manifest())
        ]

        if not request.profile.description:
            request.profile.description = card.description
        if not request.profile.readme:
            request.profile.readme = _generate_readme(card)
        if not request.profile.avatar_url:
            request.profile.avatar_url = card.icon_url

    return request


def register_to_agentverse(
    agent: AgentverseAgent, card: AgentCard | None = None, active: bool = False
):

    request = _generate_registration_request(agent, card)
    auth_header = {
        "Authorization": f"Agent {generate_agent_auth_token(Identity.from_seed(agent.uri.key, 0))}"
    }

    _register_to_agentverse(request, auth_header, agent.uri.agentverse_config)


class AgentverseA2AStarletteApplication(A2AStarletteApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register()

    @wraps(A2AStarletteApplication.build)
    def build(self, *args, **kwargs) -> Starlette:
        app = super().build(*args, **kwargs)
        app.add_route(
            name="Agentverse chat messages handler",
            path=DEFAULT_AGENTVERSE_CHAT_ENDPOINT,
            methods=["POST"],
            route=self._chat,
        )
        return app

    async def _handle_requests(self, request: Request) -> Response:
        print(f"Got an a2a message {request}")
        return await super()._handle_requests(request)

    async def _chat(self, request: Request) -> Response:
        env, msg = await _parse_chat_request(request, _agent.verify_envelope)

        if isinstance(msg, ChatAcknowledgement):
            return JSONResponse({})

        # await send_message_to_agent(
        send_message_to_agent(
            destination=env.sender,
            msg=ChatAcknowledgement(
                timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id
            ),
            sender=Identity.from_seed(_agent.uri.key, 0),
            agentverse_config=_agent.uri.agentverse_config,
        )

        if len(msg.content) == 1 and isinstance(msg.content[0], StartSessionContent):
            return JSONResponse({})

        text = ""
        for item in msg.content:
            if isinstance(item, TextContent):
                text += item.text

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
                            "text": text,
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

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse A2A agent response: {str(e)}")
            response = "Sorry, malformed response from the agent, please retry later."
        except Exception as e:
            print(f"Failed to process request by a2a agent: {str(e)}")
            response = "Sorry, agent is not reachable"

        # send the response back to the user
        av_response = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response)],
        )
        send_message_to_agent(
            destination=env.sender,
            msg=av_response,
            sender=Identity.from_seed(_agent.uri.key, 0),
            agentverse_config=_agent.uri.agentverse_config,
            session_id=env.session,
        )

        return JSONResponse({})

    def register(self):
        global _agent

        if _agent is None:
            raise RuntimeError("Not initialised.")

        register_to_agentverse(_agent, self.agent_card)


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
    track_interactions: bool = False,
):

    # instrument a2a starlette
    patch_a2a_app_builder(AgentverseA2AStarletteApplication)
    gl = inspect.stack()[1].frame.f_globals
    gl["A2AStarletteApplication"] = AgentverseA2AStarletteApplication

    # store the agent info
    global _agent
    _agent = AgentverseAgent(
        uri=AgentUri.from_str(agent),
        profile=profile,
        metadata=metadata,
        verify_envelope=(not disable_message_auth),
    )
