from uagents import Agent, Bureau, Context, Model


class Message(Model):
    text: str


ALICE_SEED = "put_alices_seed_phrase_here"
BOB_SEED = "put_bobs_seed_phrase_here"

alice = Agent(name="alice", seed=ALICE_SEED)
bob = Agent(name="bob", seed=BOB_SEED)


@alice.on_interval(period=3.0)
async def send_message(ctx: Context):
    msg = f"Hello there {bob.name}."
    await ctx.send(bob.address, Message(text=msg))


@bob.on_message(model=Message)
async def bob_message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.text}")
    msg = f"Hello there {alice.name}."
    await ctx.send(sender, Message(text=msg))


@alice.on_message(model=Message)
async def alice_message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.text}")


bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
