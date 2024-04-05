from uagents import Agent, Context, Model


class Message(Model):
    message: str


ALICE_ADDRESS = "paste_alice_address_here"
BOB_SEED = "put_your_seed_phrase_here"

print(f"Your agent's address is: {Agent(seed=BOB_SEED).address}")

AGENT_MAILBOX_KEY = "put_your_AGENT_MAILBOX_KEY_here"

bob = Agent(
    name="bob",
    seed=BOB_SEED,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)


@bob.on_interval(period=2.0)
async def send_message(ctx: Context):
    ctx.logger.info("Sending message to alice")
    await ctx.send(ALICE_ADDRESS, Message(message="Hello there alice"))


@bob.on_message(model=Message, replies=set())
async def on_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    bob.run()
