import importlib
import inspect
import sys
from functools import wraps
from typing import Type

import a2a
from a2a.server.apps import A2AStarletteApplication
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response

DEFAULT_AGENTVERSE_CHAT_ENDPOINT = "/av/chat"

_agent_key = None


async def chat(request: Request) -> Response:
    print(f"Got a chat message {request}")
    return Response({})


class AgentverseA2AStarletteApplication(A2AStarletteApplication):
    def __init__(self, *args, **kwargs):
        print(f"Using instrumented starlette app..")
        super().__init__(*args, **kwargs)
        self._agent_key = None

    @wraps(A2AStarletteApplication.build)
    def build(self, *args, **kwargs) -> Starlette:
        app = super().build(*args, **kwargs)
        app.add_route(
            name="Agentverse chat messages handler",
            path=DEFAULT_AGENTVERSE_CHAT_ENDPOINT,
            methods=["POST"],
            route=chat,
        )
        return app

    async def _handle_requests(self, request: Request) -> Response:
        print(f"Got an a2a message {request}")
        return await super()._handle_requests(request)


def patch_a2a_app_builder(new_builder: Type):
    importlib.reload(a2a)
    a2a.server.apps.A2AStarletteApplication = new_builder
    sys.modules["a2a"] = a2a


def init(agent_key: str):
    print("Instrumenting A2A App...")

    # instrument a2a starlette
    patch_a2a_app_builder(AgentverseA2AStarletteApplication)
    gl = inspect.stack()[1].frame.f_globals
    gl["A2AStarletteApplication"] = AgentverseA2AStarletteApplication

    # store the agent key
    global _agent_key
    _agent_key = agent_key
