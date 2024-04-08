from uagents import Agent, Context, Model


class Message(Model):
    message: str


BOB_SEED = "put_bobs_seed_phrase_here"

bob = Agent(
    name="bob",
    port=8001,
    seed=BOB_SEED,
    endpoint=["http://127.0.0.1:8001/submit"],
)

print(f"bob's address: {bob.address}")

@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")
    await ctx.send(sender, Message(message="Hello there alice."))


if __name__ == "__main__":
    bob.run()
