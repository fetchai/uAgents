from datetime import datetime, timezone
from uuid import uuid4

from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from uagents import Agent, Bureau, Context
from uagents.experimental.subscription import RateLimit, SubscribableProtocol

subscriber = Agent(name="Subscriber")
service_provider = Agent(name="ServiceProvider")


subs_chat_proto = SubscribableProtocol(
    storage_reference=service_provider.storage,
    identity=service_provider.identity,
    agentverse=service_provider.agentverse,
    spec=chat_protocol_spec,
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=6),
)


@subs_chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Received request request from {sender}")


@subs_chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


service_provider.include(subs_chat_proto)


@subscriber.on_interval(2)
async def request_service(ctx: Context):
    await ctx.send(
        service_provider.address,
        ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="Hello from subscriber!")],
        ),
    )


bureau = Bureau(agents=[subscriber, service_provider])


if __name__ == "__main__":
    bureau.run()
