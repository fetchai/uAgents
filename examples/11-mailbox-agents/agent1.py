from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low


class Message(Model):
    message: str


BOB_ADDRESS = "agent1qwdxsdmxus9v7ama8y95krj048286euu0vsaxq6qgzjec00xlfyevfmf3cu"

API_KEY = "my_api_key"
MAILBOX_URL = "ws://127.0.0.1:8000"


agent = Agent(
    name="alice",
    seed="alice new phrase",
    mailbox=f"{API_KEY}@{MAILBOX_URL}",
)

fund_agent_if_low(agent.wallet.address())


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    ctx.logger.info("Sending message to bob")
    await ctx.send(BOB_ADDRESS, Message(message="hello there bob"))


@agent.on_message(model=Message, replies=set())
async def on_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    agent.run()
