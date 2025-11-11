import json
import os
from typing import Any, cast

from litellm import completion
from litellm.types.utils import ModelResponse
from pydantic import BaseModel, ConfigDict
from uagents.experimental.chat_agent.tools import Tool

ASI1_API_URL = "https://api.asi1.ai/v1"
ASI1_API_KEY = os.getenv("ASI1_API_KEY", "")

DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1024
DEFAULT_SYSTEM_PROMPT = (
    "You are an AI agent built on the uAgents framework and ChatProtocol. "
    "Respond to user queries using the most relevant one of the available tools. "
    "If insufficient information is provided to invoke a tool, you may "
    "ask for more details but do not guess. "
)


class LLMParams(BaseModel):
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    tool_choice: str = "required"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    parallel_tool_calls: bool = False
    model_config = ConfigDict(extra="allow")


class LLMConfig(BaseModel):
    provider: str
    model: str
    url: str
    parameters: LLMParams
    api_key: str | None = None


asi1_config = LLMConfig(
    provider="openai",
    api_key=ASI1_API_KEY,
    model="asi1-mini",
    url=ASI1_API_URL,
    parameters=LLMParams(),
)


class LLM:
    def __init__(self, config: LLMConfig, tools: dict[str, Tool]):
        self._config = config
        self._tools = tools

    def _build_tool_specs(self) -> list[dict[str, Any]]:
        return [tool.tool_spec() for tool in self._tools.values()]

    def process(
        self,
        message_history: list[dict[str, str]],
    ) -> tuple[str, dict, str | None, dict]:
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

        kwargs = {
            "model": model_id,
            "messages": messages,
            "api_base": self._config.url,
            "api_key": self._config.api_key,
            "stream": False,
            **params_dict,
        }
        if tools_specs:
            kwargs["tools"] = tools_specs
        else:
            kwargs.pop("tool_choice", None)

        try:
            resp = cast(ModelResponse, completion(**kwargs))
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")

        msg = resp.choices[0].message.model_dump() # type: ignore
        tool_calls = msg.get("tool_calls") or []

        if tool_calls:
            call = tool_calls[0]
            msg["tool_calls"] = [call]
            fn = call.get("function", {})
            tool_name = fn.get("name")
            args_raw = fn.get("arguments", "{}")
            tool_call_id = call.get("id")

            try:
                args_dict = (
                    json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                )
            except json.JSONDecodeError:
                args_dict = {"_raw_args": args_raw}

            return (tool_name, args_dict, tool_call_id, msg)

        content_text = (msg.get("content") or "").strip()
        if content_text:
            return ("__plain_text__", {"message": content_text}, None, msg)

        raise RuntimeError("LLM returned neither tool_calls nor content.")

    def complete(self, messages: list[dict]) -> str:
        """Finalize a chat turn after tool execution."""

        model_id = f"{self._config.provider}/{self._config.model}"
        params_dict = self._config.parameters.model_dump()
        params_dict.pop("system_prompt", None)
        params_dict.pop("tool_choice", None)

        kwargs = {
            "model": model_id,
            "messages": messages,
            "api_base": self._config.url,
            "api_key": self._config.api_key,
            "stream": False,
            **params_dict,
        }

        has_tool_message = any(
            isinstance(m, dict) and m.get("role") == "tool" for m in messages
        )

        if has_tool_message:
            tools_specs = self._build_tool_specs()
            if tools_specs:
                kwargs["tools"] = tools_specs
                kwargs["tool_choice"] = "none"

        resp = cast(ModelResponse, completion(**kwargs))
        return (resp.choices[0].message.content or "").strip() # type: ignore
