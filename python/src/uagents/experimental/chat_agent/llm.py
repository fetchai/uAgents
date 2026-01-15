import json
import logging
import os
from typing import Any, cast

import litellm
from litellm import completion
from litellm.types.utils import ModelResponse
from pydantic import BaseModel, ConfigDict

from uagents.experimental.chat_agent.tools import Tool

# Suppress litellm logging
litellm.suppress_debug_info = True
logging.getLogger("LiteLLM").setLevel(logging.ERROR)


DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1024
DEFAULT_SYSTEM_PROMPT = (
    "You are an AI agent built on the uAgents framework and ChatProtocol. "
    "Respond to user queries using the most relevant one of the available tools. "
    "If insufficient information is provided to invoke a tool, you may "
    "ask for more details but do not guess."
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

    @classmethod
    def asi1(cls) -> "LLMConfig":
        api_key = os.getenv("ASI1_API_KEY")
        if api_key is None:
            raise ValueError("Please set ASI1_API_KEY environment variable.")
        return LLMConfig(
            provider="openai",
            api_key=api_key,
            model="asi1-mini",
            url="https://api.asi1.ai/v1",
            parameters=LLMParams(),
        )


class LLM:
    def __init__(self, config: LLMConfig, tools: dict[str, Tool]):
        self._config = config
        self._tools = tools

    def _build_tool_specs(self) -> list[dict[str, Any]]:
        return [tool.tool_spec() for tool in self._tools.values()]

    def _get_model_id(self) -> str:
        """Get the full model identifier."""
        return f"{self._config.provider}/{self._config.model}"

    def _get_base_kwargs(
        self, messages: list[dict], exclude_params: set[str] | None = None
    ) -> dict[str, Any]:
        """Build base kwargs for LLM completion calls."""
        params_dict = self._config.parameters.model_dump()

        # Remove excluded parameters
        if exclude_params:
            for param in exclude_params:
                params_dict.pop(param, None)

        return {
            "model": self._get_model_id(),
            "messages": messages,
            "api_base": self._config.url,
            "api_key": self._config.api_key,
            "stream": False,
            **params_dict,
        }

    def _parse_tool_call(self, tool_calls: list[dict]) -> tuple[str, dict, str | None]:
        """Parse the first tool call from LLM response."""
        call = tool_calls[0]
        fn = call.get("function", {})
        tool_name = fn.get("name")
        args_raw = fn.get("arguments", "{}")
        tool_call_id = call.get("id")

        try:
            args_dict = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
        except json.JSONDecodeError:
            args_dict = {"_raw_args": args_raw}

        return (tool_name, args_dict, tool_call_id)

    def process(
        self,
        message_history: list[dict[str, str]],
    ) -> tuple[str, dict, str | None, dict]:
        """Process a user message and determine the next action."""
        tools_specs = self._build_tool_specs()

        messages = [
            {
                "role": "system",
                "content": self._config.parameters.system_prompt,
            },
            *message_history,
        ]

        kwargs = self._get_base_kwargs(messages, exclude_params={"system_prompt"})

        # Add tools if available
        if tools_specs:
            kwargs["tools"] = tools_specs
        else:
            kwargs.pop("tool_choice", None)

        try:
            resp = cast(ModelResponse, completion(**kwargs))
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}") from e

        message_obj = resp.choices[0].message

        if isinstance(message_obj, dict):
            msg = message_obj
        else:
            msg = message_obj.model_dump()

        tool_calls = msg.get("tool_calls") or []

        if tool_calls:
            # Keep only the first tool call
            msg["tool_calls"] = [tool_calls[0]]
            tool_name, args_dict, tool_call_id = self._parse_tool_call(tool_calls)
            return (tool_name, args_dict, tool_call_id, msg)

        content_text = (msg.get("content") or "").strip()
        if content_text:
            return ("__plain_text__", {"message": content_text}, None, msg)

        raise RuntimeError("LLM returned neither tool_calls nor content.")

    def complete(self, messages: list[dict]) -> str:
        """Finalize a chat turn after tool execution."""
        kwargs = self._get_base_kwargs(
            messages, exclude_params={"system_prompt", "tool_choice"}
        )

        try:
            resp = cast(ModelResponse, completion(**kwargs))
        except Exception as e:
            raise RuntimeError(f"LLM completion call failed: {e}") from e

        return (resp.choices[0].message.content or "").strip()  # type: ignore
