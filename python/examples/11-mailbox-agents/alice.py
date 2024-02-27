from uagents import Agent, Context, Model


class Message(Model):
    message: str


# First generate a secure seed phrase (e.g. https://pypi.org/project/mnemonic/)
SEED_PHRASE = "put_your_seed_phrase_here"

# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

# Then go to https://agentverse.ai, register your agent in the Mailroom
# and copy the agent's mailbox key
AGENT_MAILBOX_KEY = "put_your_AGENT_MAILBOX_KEY_here"

# Now your agent is ready to join the agentverse!
agent = Agent(
    name="alice",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)


@agent.on_message(model=Message, replies={Message})
async def handle_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    ctx.logger.info("Sending message to bob")
    await ctx.send(sender, Message(message="hello there bob"))


if __name__ == "__main__":
    agent.run()
