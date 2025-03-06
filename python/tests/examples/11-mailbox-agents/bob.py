from uagents import Agent, Context, Model


class Message(Model):
    message: str


# Copy ALICE_ADDRESS generated in alice.py
ALICE_ADDRESS = "paste_alice_address_here"


# Now your agent is ready to join the agentverse!
agent = Agent(name="bob", port=8001, mailbox=True)


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    ctx.logger.info("Sending message to alice")
    await ctx.send(ALICE_ADDRESS, Message(message="hello there alice"))


@agent.on_message(model=Message, replies=set())
async def on_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    agent.run()
