from typing import Optional

from uagents import Agent
from uagents.experimental.chatagent.ai import LLMConfig, asione_config
from uagents.experimental.chatagent.chat_protocol import ChatProtocol
from uagents.experimental.chatagent.tools import Tool, extract_tools_from_protocol
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
            llm_config=llm_config or asione_config,
            tools=self._tools,
        )

        super().include(self._chat_proto, publish_manifest=True)

    def include(self, proto: Protocol, publish_manifest: bool = True):
        super().include(proto, publish_manifest=publish_manifest)

        new_tools = extract_tools_from_protocol(proto)
        for tool in new_tools:
            self._tools[tool.name] = tool
