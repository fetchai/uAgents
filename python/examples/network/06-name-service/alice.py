from uagents import Agent, Context, Model


class Message(Model):
    message: str


ALICE_SEED = "put_alices_seed_phrase_here"

alice = Agent(
    name="alice-0",
    seed=ALICE_SEED,
    port=8000,
    endpoint=["http://localhost:8000/submit"],
)

DOMAIN = "example.agent"


@alice.on_interval(period=5)
async def alice_interval_handler(ctx: Context):
    bob_name = "bob-0" + "." + DOMAIN
    await ctx.send(bob_name, Message(message="Hello there bob"))


if __name__ == "__main__":
    alice.run()
