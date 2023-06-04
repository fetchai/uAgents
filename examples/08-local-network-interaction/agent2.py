from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model


class Message(Model):
    message: str


RECIPIENT_ADDRESS = "agent1qwt44mq0w5gctsdcltzytksfv6g7aelf3w0k8g6z6jn8sd4hdpessle5dvv"

alice = Agent(
    name="aliceg",
    port=8000,
    seed="alice secret phraseg",
    endpoint=["http://127.0.0.1:8000/submit"],
)

fund_agent_if_low(alice.wallet.address())


@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send("bobg", Message(message="Hello there bob."))


@alice.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    alice.run()
