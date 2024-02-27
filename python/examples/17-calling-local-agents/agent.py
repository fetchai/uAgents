from uagents import Agent, Context, Bureau, Model


class Message(Model):
    text: str


agent = Agent(
    name="agent",
    seed="my local agent is here",
)
print(f"Agent address: {agent.address}")


@agent.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.text}")
    await ctx.send(sender, Message(text="Hello back!"))


if __name__ == "__main__":
    agent.run()
