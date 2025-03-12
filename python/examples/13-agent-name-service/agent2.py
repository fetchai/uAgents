from uagents import Agent, Context, Model


class Message(Model):
    message: str


alice = Agent(
    name="alice-0",
    seed="agent alice-0 secret phrase",
    port=8000,
    endpoint=["http://localhost:8000/submit"],
)

BOB_REGISTERED_ANAME = "example-bob-0"
if BOB_REGISTERED_ANAME == "BOB_REGISTERED_ANAME":
    raise ValueError("Please set the name registered by the bob agent")
DOMAIN = "agent"


@alice.on_interval(period=5)
async def alice_interval_handler(ctx: Context):
    bob_name = BOB_REGISTERED_ANAME + "." + DOMAIN
    ctx.logger.info(f"Sending message to {bob_name}...")
    await ctx.send(bob_name, Message(message="Hello there bob."))


if __name__ == "__main__":
    alice.run()
