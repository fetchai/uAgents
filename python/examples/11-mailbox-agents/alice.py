from uagents import Agent, Context, Model


class Message(Model):
    message: str


# First generate a secure seed phrase (e.g. https://pypi.org/project/mnemonic/)
SEED_PHRASE = "put_your_seed_phrase_here"

# Now your agent is ready to join the agentverse!
agent = Agent(
    name="alice",
    seed=SEED_PHRASE,
    port=8000,
    endpoint="http://agentverse.ai/v1/submit",
)


@agent.on_message(model=Message, replies={Message})
async def handle_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    ctx.logger.info("Sending message to bob")
    await ctx.send(sender, Message(message="hello there bob"))


if __name__ == "__main__":
    agent.run()
