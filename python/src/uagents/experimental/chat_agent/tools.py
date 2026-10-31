from collections.abc import Callable
from typing import Any

from uagents_core.models import ErrorMessage, Field, Model

from uagents.protocol import Protocol

# Models that must never be exposed as LLM function tools (transport / system).
_EXCLUDED_TOOL_MODELS: frozenset[type[Model]] = frozenset({ErrorMessage})

AGENT_INFO_TOOL_NAME = "AgentInfoRequest"
AGENT_INFO_TOOL_DESCRIPTION = (
    "Use this for greetings, introductions, and questions about who this agent "
    "is or what it can help with. Returns the agent's name, description, "
    "instructions, README, starter prompts, and capabilities (including each "
    "tool's arguments and reply schemas). Do not use this for requests that "
    "match another tool."
)


class AgentInfoRequest(Model):
    """Get general information about this agent."""


class AgentToolInfo(Model):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="What this tool does")
    parameters: dict = Field(..., description="JSON schema for the tool arguments")
    returns: list[dict] = Field(
        default_factory=list,
        description="JSON schemas for values this tool can send back",
    )


class AgentInfoResponse(Model):
    name: str = Field(..., description="This agent's name")
    description: str = Field(..., description="Short description of this agent")
    instructions: str = Field(..., description="How this agent is instructed to behave")
    readme: str = Field(..., description="A shortened version of the agent's README")
    starter_prompts: list[str] = Field(
        ..., description="Examples of requests this agent supports"
    )
    capabilities: list[AgentToolInfo] = Field(
        ...,
        description="Other tools this agent can use, including argument and reply schemas",
    )


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        model_cls: type[Model],
        handler: Callable[..., Any],
        returns: list[dict] | None = None,
    ):
        self.name = name
        self.description = description
        self.model_cls = model_cls
        self.handler = handler
        self.returns = returns or []

    def tool_spec(self) -> dict[str, Any]:
        schema = self.model_cls.schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }


def extract_tools_from_protocol(proto: Protocol) -> list[Tool]:
    tools: list[Tool] = []

    all_handlers: dict[str, Callable[..., Any]] = {
        **proto.signed_message_handlers,
        **proto.unsigned_message_handlers,
    }

    for digest, model_cls in proto.models.items():
        if model_cls in _EXCLUDED_TOOL_MODELS:
            continue
        handler_fn = all_handlers.get(digest)
        if handler_fn is None:
            continue

        tool_name = model_cls.__name__
        schema = model_cls.schema()
        description = (
            (model_cls.__doc__ or "").strip()
            or (handler_fn.__doc__ or "").strip()
            or schema.get("description")
            or (
                f"Handle a `{model_cls.__name__}` request for protocol "
                f"{proto.canonical_name}."
            )
        )
        returns = [
            reply_cls.schema() for reply_cls in proto.replies.get(digest, {}).values()
        ]

        tools.append(
            Tool(
                name=tool_name,
                description=description,
                model_cls=model_cls,
                handler=handler_fn,
                returns=returns,
            )
        )

    return tools
