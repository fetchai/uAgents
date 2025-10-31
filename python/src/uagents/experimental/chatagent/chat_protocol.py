from datetime import datetime, timezone
from uuid import uuid4

from pydantic.v1 import ValidationError
from uagents import Context
from uagents.experimental.chatagent.ai import LLM, LLMConfig
from uagents.experimental.chatagent.tools import Tool
from uagents.protocol import Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)


def _create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=content)


class ChatProtocol(Protocol):
    def __init__(
        self,
        *,
        llm_config: LLMConfig,
        tools: dict[str, Tool],
        name: str = "ChatProto-LLM",
        version: str = "0.1.0",
    ):
        super().__init__(name=name, version=version, spec=chat_protocol_spec)

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

            session = ctx.session
            messages: list[dict] = []

            if ctx._message_history is not None:
                try:
                    past_entries = ctx._message_history.get_session_messages(session)
                    for entry in past_entries:
                        if entry.sender != ctx.agent.address:
                            messages.append(
                                {
                                    "role": "user",
                                    "content": entry.payload,
                                }
                            )
                except Exception as e:
                    ctx.logger.warning(f"Could not load message history: {e}")

            messages.append(
                {
                    "role": "user",
                    "content": user_text,
                }
            )

            try:
                tool_name, arg_dict = self._llm.process(messages)

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

            if isinstance(result, str):
                return await self.send_text(ctx, sender, result)

            return await self.send_text(ctx, sender, str(result))

    async def send_text(
        self,
        ctx: Context,
        recipient: str,
        text: str,
        *,
        end_session: bool = True,
    ):
        return await ctx.send(
            recipient,
            _create_text_chat(text, end_session=end_session),
        )
