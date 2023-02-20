from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low, register_agent_with_mailbox


class Message(Model):
    message: str


BOB_ADDRESS = "agent1q2kxet3vh0scsf0sm7y2erzz33cve6tv5uk63x64upw5g68kr0chkv7hw50"

agent = Agent(
    name="alice",
    seed="alice secret phrase",
    mailbox="my_api_key@ws://127.0.0.1:8000",
)

fund_agent_if_low(agent.wallet.address())
register_agent_with_mailbox(agent, "alice@uagent.ai")


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    ctx.logger.info("Sending message to bob")
    await ctx.send(BOB_ADDRESS, Message(message="hello there bob"))


@agent.on_message(model=Message, replies=set())
async def on_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    agent.run()
