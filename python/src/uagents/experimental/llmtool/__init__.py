import json
from typing import Any, Callable, Literal, Tuple

from litellm import completion
from pydantic import BaseModel, ConfigDict
from uagents.protocol import Protocol
from uagents_core.models import Model

OPENAI_API_URL = "https://api.openai.com/v1"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ASIONE_API_URL = "https://api.asi1.ai/v1"

DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1024


class LLMParams(BaseModel):
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    tool_choice: str = "auto"
    system_prompt: str = (
        "You are an assistant running inside an on-chain agent. "
        "If one of the provided tools can fulfill the request, "
        "call it with correct JSON arguments. "
        "If none apply, answer in plain text to the user."
    )
    model_config = ConfigDict(extra="allow")


class LLMConfig(BaseModel):
    provider: str = Literal["asi1", "openai", "claude"]
    api_key: str
    model: str
    url: str
    parameters: LLMParams


openai_config = LLMConfig(
    provider="openai",
    api_key="YOUR_OPENAI_API_KEY",
    model="gpt-4o-mini",
    url=OPENAI_API_URL,
    parameters=LLMParams(),
)

claude_config = LLMConfig(
    provider="anthropic",
    api_key="YOUR_ANTHROPIC_API_KEY",
    model="claude-3-5-haiku-latest",
    url=ANTHROPIC_API_URL,
    parameters=LLMParams(),
)

asione_config = LLMConfig(
    provider="openai",
    api_key="YOUR_ASI1_API_KEY",
    model="asi1-mini",
    url=ASIONE_API_URL,
    parameters=LLMParams(),
)


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        model_cls: type[Model],
        handler: Callable[..., Any],
    ):
        self.name = name
        self.description = description
        self.model_cls = model_cls
        self.handler = handler

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
        handler_fn = all_handlers.get(digest)
        if handler_fn is None:
            continue

        tool_name = model_cls.__name__
        description = f"Handle a `{model_cls.__name__}` request for protocol {proto.canonical_name}."

        tools.append(
            Tool(
                name=tool_name,
                description=description,
                model_cls=model_cls,
                handler=handler_fn,
            )
        )

    return tools


class LLM:
    def __init__(self, config: LLMConfig, tools: dict[str, Tool]):
        self._config = config
        self._tools = tools

    def _build_tool_specs(self) -> list[dict[str, Any]]:
        return [tool.tool_spec() for tool in self._tools.values()]

    def process(
        self,
        message_history: list[dict[str, str]],
    ) -> Tuple[str, dict]:
        tools_specs = self._build_tool_specs()
        model_id = f"{self._config.provider}/{self._config.model}"

        messages = [
            {
                "role": "system",
                "content": self._config.parameters.system_prompt,
            },
            *message_history,
        ]

        params_dict = self._config.parameters.model_dump()
        if "system_prompt" in params_dict:
            params_dict.pop("system_prompt")

        try:
            resp = completion(
                model=model_id,
                messages=messages,
                tools=tools_specs,
                api_base=self._config.url,
                api_key=self._config.api_key,
                **params_dict,
            )
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")

        msg = resp["choices"][0]["message"]
        tool_calls = msg.get("tool_calls") or []

        if len(tool_calls) > 0:
            call = tool_calls[0]
            fn = call.get("function", {})
            tool_name = fn.get("name")
            args_raw = fn.get("arguments", "{}")

            try:
                args_dict = (
                    json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                )
            except json.JSONDecodeError:
                args_dict = {"_raw_args": args_raw}

            return (tool_name, args_dict)

        content_text = (msg.get("content") or "").strip()
        if content_text:
            return ("__plain_text__", {"message": content_text})

        raise RuntimeError("LLM returned neither tool_calls nor content.")
