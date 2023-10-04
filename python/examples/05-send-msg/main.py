from uagents import Agent, Context, Bureau, Model


class Message(Model):
    text: str


alice = Agent(name="alice", seed="alice recovery phrase")
bob = Agent(name="bob", seed="bob recovery phrase")


@alice.on_interval(period=2.0)
async def send_message(ctx: Context):
    msg = f"Hello there {bob.name} my name is {alice.name}."
    await ctx.send(bob.address, Message(text=msg))


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.text}")


bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
