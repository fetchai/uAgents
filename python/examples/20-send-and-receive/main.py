from uagents import Agent, Bureau, Context, Model


class Message(Model):
    message: str


alice = Agent(name="alice")
bob = Agent(name="bob")
clyde = Agent(name="clyde")


@alice.on_interval(period=5.0)
async def send_message(ctx: Context):
    msg = Message(message="Hey Bob, how's Clyde?")
    reply, status = await ctx.send_and_receive(bob.address, msg, response_type=Message)
    if isinstance(reply, Message):
        ctx.logger.info(f"Received awaited response from bob: {reply.message}")
    else:
        ctx.logger.info(f"Failed to receive response from bob: {status}")


@bob.on_message(model=Message)
async def handle_message_and_reply(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message: {msg.message}")
    new_msg = Message(message="How are you, Clyde?")
    reply, status = await ctx.send_and_receive(
        clyde.address, new_msg, response_type=Message
    )
    if isinstance(reply, Message):
        ctx.logger.info(f"Received awaited response from clyde: {reply.message}")
        await ctx.send(sender, Message(message="Clyde is doing alright!"))
    else:
        ctx.logger.info(f"Failed to receive response from clyde: {status}")


@clyde.on_message(model=Message)
async def handle_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")
    await ctx.send(sender, Message(message="I'm doing alright!"))


bureau = Bureau([alice, bob, clyde])

if __name__ == "__main__":
    bureau.run()
