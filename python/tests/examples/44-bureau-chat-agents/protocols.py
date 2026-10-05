from uagents import Context, Field, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    chat_protocol_spec,
)

word_counter_proto = Protocol(name="WordCounter", version="0.1.0")


class WordCountRequest(Model):
    text: str = Field(..., description="Text to count words in")


class WordCountResponse(Model):
    count: int = Field(..., description="Number of words in the text")


def _count_words(text: str) -> int:
    return len([w for w in text.split() if w.strip()])


@word_counter_proto.on_message(WordCountRequest)
async def handle_word_count(ctx: Context, sender: str, msg: WordCountRequest):
    count = _count_words(msg.text)
    await ctx.send(sender, WordCountResponse(count=count))


listen_proto = Protocol(spec=chat_protocol_spec)


@listen_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


@listen_proto.on_message(ChatMessage)
async def log_expert_reply(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(acknowledged_msg_id=msg.msg_id),
    )
    ctx.logger.info("Reply from %s: %s", sender, msg.text())
