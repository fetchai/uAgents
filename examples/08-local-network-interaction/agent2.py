from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model


class Message(Model):
    message: str


alice = Agent(
    name="alice2",
    port=8000,
    seed="alice secret phrase2",
    endpoint=["http://127.0.0.1:8000/submit"],
)

fund_agent_if_low(alice.wallet.address())


@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send("bob", Message(message="Hello there bob."))


@alice.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    alice.run()
