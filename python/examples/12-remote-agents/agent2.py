"""
Counterpart for the remote connection example in agent1.py.
"""
from uagents import Agent, Context, Model


class Message(Model):
    message: str


bob = Agent(
    name="bob",
    port=8001,
    seed="agent2 secret seed phrase",
    endpoint=["http://127.0.0.1:8001/submit"],
)

ALICE_ADDRESS = "agent1qv2l7qzcd2g2rcv2p93tqflrcaq5dk7c2xc7fcnfq3s37zgkhxjmq5mfyvz"


@bob.on_interval(period=5.0)
async def send_to_alice(ctx: Context):
    """Send a message to alice every 5 seconds."""
    ctx.logger.info("Sending message to alice")
    await ctx.send(ALICE_ADDRESS, Message(message="hello there alice"))


if __name__ == "__main__":
    bob.run()
