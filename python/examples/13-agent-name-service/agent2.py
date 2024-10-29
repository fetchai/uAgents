from uagents import Agent, Context, Model


class Message(Model):
    text: str


alice = Agent(
    name="alice",
    seed="agent alice-0 secret phrase",
    port=8000,
    endpoint=["http://localhost:8000/submit"],
)

DOMAIN = "bob.example.agent"


@alice.on_interval(period=5)
async def alice_interval_handler(ctx: Context):
    bob_name = DOMAIN
    ctx.logger.info(f"Sending message to {bob_name}...")
    await ctx.send(bob_name, Message(text="Hello there bob."))


if __name__ == "__main__":
    alice.run()
