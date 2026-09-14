from typing import Optional

from uagents_core.registration import AgentProfile

from uagents import Agent, Context
from uagents.experimental.chat_agent.llm import LLMConfig, LLMParams
from uagents.experimental.chat_agent.protocol import ChatProtocol
from uagents.experimental.chat_agent.tools import (
    AGENT_INFO_TOOL_DESCRIPTION,
    AGENT_INFO_TOOL_NAME,
    AgentInfoRequest,
    AgentInfoResponse,
    AgentToolInfo,
    Tool,
    extract_tools_from_protocol,
)
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
        self._chat_instructions = instructions

        super().__init__(
            *args,
            publish_agent_details=publish_agent_details,
            store_message_history=store_message_history,
            **kwargs,
        )

        self._tools: dict[str, Tool] = {}
        self._register_agent_info_tool()

        self._chat_proto = ChatProtocol(
            llm_config=llm_config or LLMConfig.asi1(),
            tools=self._tools,
            instructions=instructions,
            agent_name=self.name,
        )

        super().include(self._chat_proto, publish_manifest=True)

    def _register_agent_info_tool(self) -> None:
        async def handle_agent_info(
            ctx: Context, sender: str, _msg: AgentInfoRequest
        ) -> None:
            capabilities = [
                AgentToolInfo(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.model_cls.schema(),
                    returns=tool.returns,
                )
                for name, tool in self._tools.items()
                if name != AGENT_INFO_TOOL_NAME
            ]
            await ctx.send(
                sender,
                AgentInfoResponse(
                    name=self.name,
                    description=self._description or "",
                    instructions=(self._chat_instructions or "").strip(),
                    capabilities=capabilities,
                ),
            )

        self._tools[AGENT_INFO_TOOL_NAME] = Tool(
            name=AGENT_INFO_TOOL_NAME,
            description=AGENT_INFO_TOOL_DESCRIPTION,
            model_cls=AgentInfoRequest,
            handler=handle_agent_info,
        )

    def _build_registration_profile(self) -> AgentProfile:
        profile = super()._build_registration_profile()
        if self._starter_prompts is None:
            return profile
        return profile.model_copy(update={"starter_prompts": self._starter_prompts})

    def include(self, protocol: Protocol, publish_manifest: bool = True):
        new_tools = extract_tools_from_protocol(protocol)
        for tool in new_tools:
            if tool.name == AGENT_INFO_TOOL_NAME:
                raise ValueError(
                    f"'{AGENT_INFO_TOOL_NAME}' is reserved by ChatAgent."
                )

        super().include(protocol, publish_manifest=publish_manifest)

        for tool in new_tools:
            self._tools[tool.name] = tool
