from nexus.setup import fund_agent_if_low
from nexus import Agent, Context, Model


class Message(Model):
    message: str


RECIPIENT_ADDRESS = "agent1q2sec3utj4a8xl8le8x2dy90f33fnlunaatxamjpepz0zk99qqttj97526g"

agent = Agent(
    name="alice",
    port=8000,
    seed="agent1 secret phrase",
    endpoint="http://127.0.0.1:8000/submit",
)

fund_agent_if_low(agent.wallet.address())


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send(RECIPIENT_ADDRESS, Message(message="hello there bob"))


@agent.on_message(model=Message)
async def on_message(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")


if __name__ == "__main__":
    agent.run()
