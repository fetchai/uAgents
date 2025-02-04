from uagents import Agent, Context, Model


class Message(Model):
    message: str


# Now your agent is ready to join the agentverse!
agent = Agent(name="alice", mailbox=True)


@agent.on_message(model=Message, replies=Message)
async def handle_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    ctx.logger.info("Sending message to bob")
    await ctx.send(sender, Message(message="hello there bob"))


if __name__ == "__main__":
    agent.run()
