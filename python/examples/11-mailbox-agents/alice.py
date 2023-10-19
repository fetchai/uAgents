from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low


class Message(Model):
    message: str


# First generate a secure seed phrase (e.g. https://pypi.org/project/mnemonic/)
SEED_PHRASE = "put_your_xxx"

# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

# Then sign up at https://agentverse.ai to get an API key and register your agent
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYXBpLWtleSIsIm5vbmNlIjoiZmViZjY1NzAtZTQ0Yy00NjNjLTg4ZDctZmIzMWQwODQ2NzA1Iiwic3ViIjoiNWYxYTE5MGNlMThjZGU2YzJiM2UzMjlmZWEzZWQ1MmIxYTI0MzVjNzY2YWQyMWI5IiwiZXhwIjoxNzA1NDk3NjM2fQ.W4NAtp84O2ernWr0Y3t4yomm4vfqJFF1Y-09BD58UJY"


# Now your agent is ready to join the agentverse!
agent = Agent(
    name="alice",
    seed=SEED_PHRASE,
    mailbox=f"{API_KEY}@https://agentverse.ai",
)

fund_agent_if_low(agent.wallet.address())


@agent.on_message(model=Message, replies={Message})
async def handle_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

    # send the response
    ctx.logger.info("Sending message to bob")
    await ctx.send(sender, Message(message="hello there bob"))


if __name__ == "__main__":
    agent.run()
