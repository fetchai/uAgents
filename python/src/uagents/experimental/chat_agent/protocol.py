import json
from datetime import datetime, timezone
from typing import cast

from pydantic.v1 import ValidationError
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
from uagents_core.types import DeliveryStatus, MsgStatus

from uagents import Context, Model
from uagents.config import DEFAULT_ENVELOPE_TIMEOUT_SECONDS
from uagents.context import ExternalContext
from uagents.experimental.chat_agent.llm import LLM, LLMConfig
from uagents.experimental.chat_agent.tools import Tool
from uagents.protocol import Protocol

FINAL_SYSTEM_PROMPT = (
    "You are generating the final reply after a tool has already been executed. "
    "Your only job is to convert the provided information into a clear, plain, "
    "user-facing response. "
    "Do not call tools. "
    "Do not try to retrieve, infer, or search for missing information. "
    "Do not output XML, JSON, tags like <tool_call>, function calls, code, or "
    "any structured markup. "
    "Do not explain internal reasoning or mention tool execution unless it is "
    "necessary for the answer. "
    "Use only the information already provided in the messages you receive. "
    "If the information is incomplete, still produce the best possible "
    "plain-language response based only on what is available. "
    "Only ask for clarification if a usable answer cannot be given from the "
    "provided information. "
    "Return only the final human-readable answer."
)


def build_llm_message_history(ctx: Context) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []

    for entry in ctx.session_history() or []:
        payload = entry.payload
        if not payload:
            continue

        try:
            hist_msg = ChatMessage.parse_raw(payload)
        except Exception:
            continue

        text = hist_msg.text().strip()
        if not text:
            continue

        role = "assistant" if entry.sender == ctx.agent.address else "user"
        history.append({"role": role, "content": text})

    return history


class ToolContext(ExternalContext):
    def __init__(self, base: ExternalContext, sender: str):
        self.__dict__ = base.__dict__.copy()

        self._tool_sender = sender
        self._captured_messages: list[Model] = []

    @property
    def captured_messages(self) -> list[Model]:
        return self._captured_messages

    async def send(
        self,
        destination: str,
        message: Model,
        timeout: int = DEFAULT_ENVELOPE_TIMEOUT_SECONDS,
    ) -> MsgStatus:
        if destination == self._tool_sender:
            self._captured_messages.append(message)
            return MsgStatus(
                status=DeliveryStatus.DELIVERED,
                detail="Captured tool output",
                destination=destination,
                endpoint="",
                session=self.session,
            )

        return await super().send(destination, message, timeout=timeout)


class ChatProtocol(Protocol):
    def __init__(
        self,
        *,
        llm_config: LLMConfig,
        tools: dict[str, Tool],
        instructions: str | None = None,
    ):
        super().__init__(spec=chat_protocol_spec)

        self._llm = LLM(config=llm_config, tools=tools, instructions=instructions)
        self._tools = tools

        @self.on_message(ChatAcknowledgement)
        async def _ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
            ctx.logger.debug(
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

            msg_text = msg.text().strip()
            if not msg_text:
                return

            msg_dict = {"role": "user", "content": msg_text}
            if ctx._message_history is None:
                messages = [msg_dict]
            else:
                messages = build_llm_message_history(ctx)
                # Session history should already include incoming message
                # if not (e.g. first message edge cases), append so process/complete never see [].
                if (
                    not messages
                    or messages[-1].get("role") != "user"
                    or messages[-1].get("content") != msg_text
                ):
                    messages = [*messages, msg_dict]

            try:
                tool_name, arg_dict, tool_call_id, _ = await self._llm.process(messages)

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
                result = await self.use_tool(tool, ctx, sender, parsed_msg)
            except Exception as err:
                ctx.logger.error(f"Handler error: {err}")
                return await self.send_text(
                    ctx,
                    sender,
                    "Sorry, I couldn't process your request. Please try again later.",
                )

            tool_result_message = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps(result),
            }

            followup_messages = [
                {"role": "system", "content": FINAL_SYSTEM_PROMPT},
                msg_dict,
                tool_result_message,
            ]

            final_text = await self._llm.complete(followup_messages)

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

    async def use_tool(
        self,
        tool: Tool,
        ctx: Context,
        sender: str,
        parsed_msg,
    ):
        tool_ctx = ToolContext(cast(ExternalContext, ctx), sender)
        await tool.handler(tool_ctx, sender, parsed_msg)

        return [m.model_dump() for m in tool_ctx.captured_messages]
