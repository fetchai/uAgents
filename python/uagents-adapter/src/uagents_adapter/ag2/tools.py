"""AG2 (formerly AutoGen) adapter for uAgents.

Wraps AG2 multi-agent conversations as a uAgent registered on
Agentverse, following the same pattern as the CrewAI and LangChain
adapters.
"""

import logging
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from uagents import Context, Model, Protocol

from uagents_adapter.common import (
    BaseRegisterTool,
    BaseRegisterToolInput,
    ResponseMessage,
    create_text_chat,
)

logger = logging.getLogger(__name__)


class QueryMessage(Model):
    """Message model for incoming queries."""

    query: str


class AG2RegisterToolInput(BaseRegisterToolInput):
    """Input schema for AG2RegisterTool.

    Args:
        agent_runner: Callable that accepts a query string and
            returns the AG2 conversation result as a string.
            The callable should create fresh agents per call
            to avoid state leakage.

    Unlike other adapters that accept a single framework
    object, AG2 multi-agent conversations require composing
    multiple ConversableAgents, a Pattern, and
    ContextVariables — there is no single object that
    encapsulates a runnable workflow. The callable interface
    lets the user own that setup and ensures agents are
    created fresh per request.
    """

    agent_runner: Callable[[str], str] = Field(
        ...,
        description=(
            "Callable that runs AG2 agents on a query and "
            "returns the result string."
        ),
    )

    class Config:
        arbitrary_types_allowed = True


class AG2RegisterTool(BaseRegisterTool):
    """Register AG2 agents as a uAgent on Agentverse.

    Example:
        from autogen import ConversableAgent, LLMConfig
        from autogen.agentchat import initiate_group_chat
        from autogen.agentchat.group.patterns import AutoPattern
        from uagents_adapter import AG2RegisterTool

        llm_config = LLMConfig({"model": "gpt-4o-mini", ...})

        def run_research(query: str) -> str:
            researcher = ConversableAgent(
                name="researcher", llm_config=llm_config, ...
            )
            writer = ConversableAgent(
                name="writer", llm_config=llm_config, ...
            )
            user = ConversableAgent(
                name="user", human_input_mode="NEVER"
            )
            pattern = AutoPattern(
                initial_agent=researcher,
                agents=[researcher, writer],
                user_agent=user,
                group_manager_args={"llm_config": llm_config},
            )
            result, ctx, last = initiate_group_chat(
                pattern=pattern,
                messages=query,
                max_rounds=10,
            )
            for msg in reversed(result.chat_history):
                content = msg.get("content", "")
                if content and "TERMINATE" not in content:
                    return content
            return "Complete."

        tool = AG2RegisterTool()
        tool.invoke({
            "agent_runner": run_research,
            "name": "ag2-research-team",
            "port": 8001,
            "description": "Research team powered by AG2",
            "api_token": os.environ["AGENTVERSE_API_KEY"],
        })
    """

    name: str = "AG2RegisterTool"
    description: str = (
        "Register AG2 (formerly AutoGen) agents as a uAgent "
        "on Agentverse."
    )
    args_schema: type[BaseModel] = AG2RegisterToolInput

    def _run(
        self,
        name: str,
        port: int | None = None,
        description: str = "",
        api_token: str | None = None,
        ai_agent_address: str | None = None,
        mailbox: bool = True,
        agent_runner: Callable[[str], str] | None = None,
        **kwargs: Any,
    ) -> str:
        if agent_runner is None:
            return "Error: agent_runner is required."

        if port is None or port <= 0:
            port = self._find_available_port()
        agent = self._create_agent(name, port, mailbox)

        # --- Chat protocol ---
        chat_proto = Protocol(name="ag2-chat")

        @chat_proto.on_message(QueryMessage)
        async def handle_query(
            ctx: Context, sender: str, msg: QueryMessage
        ):
            logger.info(
                "AG2 agent received query: %s", msg.query
            )
            try:
                result = await _run_in_thread(
                    agent_runner, msg.query
                )
            except Exception as e:
                logger.exception("AG2 agent failed")
                result = f"Error: {e}"

            await ctx.send(
                sender, ResponseMessage(response=result)
            )

        # --- Agentverse chat protocol ---
        agentverse_chat = Protocol(name="ag2-agentverse")

        _chat_handlers_registered = False
        try:
            from uagents_core.contrib.protocols.chat import (
                ChatAcknowledgement,
                ChatMessage,
            )

            @agentverse_chat.on_message(ChatMessage)
            async def handle_chat(
                ctx: Context, sender: str, msg: ChatMessage
            ):
                # Extract text from chat message
                query = ""
                for item in msg.content:
                    if hasattr(item, "text"):
                        query = item.text
                        break

                if not query:
                    await ctx.send(
                        sender,
                        create_text_chat(
                            "No query provided.",
                            end_session=True,
                        ),
                    )
                    return

                # Acknowledge receipt
                await ctx.send(
                    sender,
                    ChatAcknowledgement(
                        acknowledged_msg_id=msg.msg_id
                    ),
                )

                try:
                    result = await _run_in_thread(
                        agent_runner, query
                    )
                except Exception as e:
                    result = f"Error: {e}"

                await ctx.send(
                    sender,
                    create_text_chat(
                        result, end_session=True
                    ),
                )

            _chat_handlers_registered = True
        except ImportError:
            logger.debug(
                "Chat dialogue not available, skipping"
            )

        agent.include(chat_proto)
        if _chat_handlers_registered:
            agent.include(agentverse_chat)

        # Start agent in a background thread
        import threading
        import time

        agent_info = {
            "name": name,
            "uagent": agent,
            "port": port,
            "description": description,
        }

        thread = threading.Thread(
            target=self._start_uagent_with_asyncio,
            args=(agent_info,),
            daemon=True,
        )
        thread.start()
        time.sleep(0.5)

        # Register with Agentverse
        if api_token:
            agent_info["api_token"] = api_token
            agent_info["ai_agent_address"] = ai_agent_address
            self._register_with_agentverse(agent_info)

        return (
            f"AG2 agent '{name}' registered on port {port}. "
            f"Address: {agent.address}"
        )

    async def _arun(self, **kwargs: Any) -> str:
        import asyncio

        return await asyncio.to_thread(self._run, **kwargs)


async def _run_in_thread(
    runner: Callable[[str], str], query: str
) -> str:
    """Run a synchronous AG2 callable in a thread to avoid
    blocking the async event loop."""
    import asyncio

    return await asyncio.to_thread(runner, query)
