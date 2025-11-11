from typing import Optional

from uagents import Agent
from uagents.experimental.chat_agent.llm import LLMConfig, asi1_config
from uagents.experimental.chat_agent.protocol import ChatProtocol
from uagents.experimental.chat_agent.tools import Tool, extract_tools_from_protocol
from uagents.protocol import Protocol


class ChatAgent(Agent):
    def __init__(
        self,
        *args,
        llm_config: Optional[LLMConfig] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._tools: dict[str, Tool] = {}

        self._chat_proto = ChatProtocol(
            llm_config=llm_config or asi1_config,
            tools=self._tools,
        )

        super().include(self._chat_proto, publish_manifest=True)

    def include(self, protocol: Protocol, publish_manifest: bool = True):
        super().include(protocol, publish_manifest=publish_manifest)

        new_tools = extract_tools_from_protocol(protocol)
        for tool in new_tools:
            self._tools[tool.name] = tool
