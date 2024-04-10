from uagents import Agent, Context, Model


class Message(Model):
    message: str


ALICE_ADDRESS = "put_alice_address_here"
BOB_SEED = "put_your_seed_phrase_here"

bob = Agent(
    name="bob",
    port=8001,
    seed=BOB_SEED,
    endpoint=["http://127.0.0.1:8001/submit"],
)


@bob.on_interval(period=5.0)
async def send_message(ctx: Context):
    ctx.logger.info("Sending message to alice")
    await ctx.send(ALICE_ADDRESS, Message(message="hello there alice"))


if __name__ == "__main__":
    bob.run()
