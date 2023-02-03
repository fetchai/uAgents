from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low


class Message(Model):
    message: str


AGENT1_ADDRESS = "agent1qv2l7qzcd2g2rcv2p93tqflrcaq5dk7c2xc7fcnfq3s37zgkhxjmq5mfyvz"
AGENT2_ADDRESS = "agent1qv73me5ql7kl30t0grehalj0aau0l4hpthp4m5q9v4qk2hz8h63vzpgyadp"

agent = Agent(
    name="alice",
    seed="agent1 secret phrase",
    mailbox="my_api_key",
)

fund_agent_if_low(agent.wallet.address())


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send(AGENT2_ADDRESS, Message(message="hello there bob"))


@agent.on_message(model=Message, replies=set())
async def on_message(ctx: Context, sender: str, msg: Message):
    print(f"[{ctx.name:5}] From: {sender} {msg.message}")


if __name__ == "__main__":
    agent.run()
