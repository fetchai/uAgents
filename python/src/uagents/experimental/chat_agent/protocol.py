import json
from datetime import datetime, timezone

from pydantic.v1 import ValidationError
from uagents import Context
from uagents.experimental.chat_agent.llm import LLM, LLMConfig
from uagents.experimental.chat_agent.tools import Tool
from uagents.protocol import Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    AgentContent,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)


class ChatProtocol(Protocol):
    def __init__(
        self,
        *,
        llm_config: LLMConfig,
        tools: dict[str, Tool],
    ):
        super().__init__(spec=chat_protocol_spec)

        self._llm = LLM(config=llm_config, tools=tools)
        self._tools = tools

        @self.on_message(ChatAcknowledgement)
        async def _ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
            ctx.logger.info(
                f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
            )

        @self.on_message(ChatMessage)
        async def _chat_handler(ctx: Context, sender: str, msg: ChatMessage):
            await ctx.send(
                sender,
                ChatAcknowledgement(
                    timestamp=datetime.now(timezone.utc),
                    acknowledged_msg_id=msg.msg_id,
                ),
            )

            if any(isinstance(item, StartSessionContent) for item in msg.content):
                ctx.logger.info(f"Got a start session message from {sender}")

            user_text = msg.text()
            if not user_text:
                return

            messages: list[dict] = []

            session_history = ctx.session_history()
            if session_history is not None:
                for entry in session_history:
                    role = "agent" if entry.sender == ctx.agent.address else "user"
                    messages.append(
                        {
                            "role": role,
                            "content": entry.payload,
                        }
                        )

            messages.append(
                {
                    "role": "user",
                    "content": user_text,
                }
            )

            try:
                tool_name, arg_dict, tool_call_id, assistant_msg = self._llm.process(
                    messages
                )

            except Exception as e:
                ctx.logger.error(f"LLM failed: {e}")
                return await self.send_text(
                    ctx, sender, f"Sorry, I couldn't process that: {e}"
                )

            if tool_name == "__plain_text__":
                return await self.send_text(ctx, sender, arg_dict["message"])

            tool = self._tools.get(tool_name)
            if tool is None:
                return await self.send_text(
                    ctx,
                    sender,
                    f"Sorry, I don't have a handler for '{tool_name}'.",
                )

            try:
                parsed_msg = tool.model_cls.model_validate(arg_dict)
            except ValidationError as ve:
                ctx.logger.error(f"Validation error: {ve}")
                return await self.send_text(
                    ctx,
                    sender,
                    (
                        "I couldn't interpret that into the expected format. "
                        f"Please try again: {arg_dict}"
                    ),
                )

            try:
                result = await tool.handler(ctx, sender, parsed_msg)
            except Exception as err:
                ctx.logger.error(f"Handler error: {err}")
                return await self.send_text(
                    ctx,
                    sender,
                    "Sorry, I couldn't process your request. Please try again later.",
                )

            if hasattr(result, "model_dump"):
                tool_content = json.dumps(result.model_dump())
            elif isinstance(result, (dict, list)):
                tool_content = json.dumps(result)
            else:
                tool_content = json.dumps({"result": str(result)})

            tool_result_message = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": tool_content,
            }
            followup_messages = [
                {
                    "role": "system",
                    "content": self._llm._config.parameters.system_prompt,
                },
                *messages,
                assistant_msg,
                tool_result_message,
            ]
            final_text = self._llm.complete(followup_messages)
            return await self.send_text(ctx, sender, final_text)

    async def send_text(
        self,
        ctx: Context,
        recipient: str,
        text: str,
        *,
        end_session: bool = False,
    ):
        content: list[AgentContent] = [TextContent(type="text", text=text)]
        if end_session:
            content.append(EndSessionContent(type="end-session"))
        return await ctx.send(recipient, ChatMessage(content=content))
