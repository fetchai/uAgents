from uagents import Agent, Context, Model


class Message(Model):
    message: str


BOB_ADDRESS = "put_BOB_ADDRESS_here"

ALICE_SEED = "put_alices_seed_phrase_here"

alice = Agent(
    name="alice",
    port=8000,
    seed=ALICE_SEED,
    endpoint=["http://127.0.0.1:8000/submit"],
)


@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send(BOB_ADDRESS, Message(message="Hello there bob."))


@alice.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    alice.run()
