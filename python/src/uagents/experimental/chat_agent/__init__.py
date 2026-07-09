from typing import Optional

from uagents_core.registration import AgentProfile

from uagents import Agent
from uagents.experimental.chat_agent.llm import LLMConfig, LLMParams
from uagents.experimental.chat_agent.protocol import ChatProtocol
from uagents.experimental.chat_agent.tools import Tool, extract_tools_from_protocol
from uagents.protocol import Protocol

__all__ = ["ChatAgent", "LLMConfig", "LLMParams"]


class ChatAgent(Agent):
    def __init__(
        self,
        *args,
        llm_config: Optional[LLMConfig] = None,
        instructions: str | None = None,
        publish_agent_details: bool = True,
        store_message_history: bool = True,
        starter_prompts: list[str] | None = None,
        **kwargs,
    ):
        self._starter_prompts = starter_prompts

        super().__init__(
            *args,
            publish_agent_details=publish_agent_details,
            store_message_history=store_message_history,
            **kwargs,
        )

        self._tools: dict[str, Tool] = {}

        self._chat_proto = ChatProtocol(
            llm_config=llm_config or LLMConfig.asi1(),
            tools=self._tools,
            instructions=instructions,
        )

        super().include(self._chat_proto, publish_manifest=True)

    def _build_registration_profile(self) -> AgentProfile:
        profile = super()._build_registration_profile()
        if self._starter_prompts is None:
            return profile
        return profile.model_copy(update={"starter_prompts": self._starter_prompts})

    def include(self, protocol: Protocol, publish_manifest: bool = True):
        super().include(protocol, publish_manifest=publish_manifest)

        new_tools = extract_tools_from_protocol(protocol)
        for tool in new_tools:
            self._tools[tool.name] = tool
