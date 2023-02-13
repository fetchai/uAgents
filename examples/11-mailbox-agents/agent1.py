from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low


class Message(Model):
    message: str


BOB_ADDRESS = "agent1q2kxet3vh0scsf0sm7y2erzz33cve6tv5uk63x64upw5g68kr0chkv7hw50"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZ2VudEBmZXRjaC5haSIsImV4cCI6MTY3NjMwOTY0Nn0.uZRrJdZoxupWyLsLDjd8oZ8h5x_u0jL9UThftGeImKE"  # pylint: disable=line-too-long


agent = Agent(
    name="alice",
    seed="alice secret phrase",
    mailbox=API_KEY,
)

fund_agent_if_low(agent.wallet.address())


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send(BOB_ADDRESS, Message(message="hello there bob"))


@agent.on_message(model=Message, replies=set())
async def on_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    agent.run()
