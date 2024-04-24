### testing code

from uagents import Agent, Context, Model, Protocol
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType


class TestRequest(Model):
    message: str


class Response(Model):
    text: str


class Message(Model):
    message: str = Field(description="Your Message.")


agent = Agent(
    name="your_agent_name_here",
    seed="your_agent_seed_here",
    port=8001,
    endpoint="http://localhost:8001/submit",
)


agent_protocol = Protocol(
    name="your_agent_name_here",
)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Hello World")


@agent_protocol.on_message(model=Message, replies={UAgentResponse})
async def message_handler(ctx: Context, sender: str, query: Message):
    ctx.logger.info("Message received")
    try:
        ctx.logger.info(res)
        await ctx.send(
            sender,
            UAgentResponse(
                message=(f":Sent message {query.message}"),
                type=UAgentResponseType.FINAL,
            ),
        )
    except Exception:
        await ctx.send(
            sender,
            UAgentResponse(
                message=(f":Failed to send message {query.message}"),
                type=UAgentResponseType.FINAL,
            ),
        )


agent.include(agent_protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
