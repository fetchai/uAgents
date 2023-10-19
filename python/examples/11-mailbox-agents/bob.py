from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low


class Message(Model):
    message: str


# Copy ALICE_ADDRESS generated in alice.py
ALICE_ADDRESS = "agent1q0z5xvmagqtg052zdcks3lpgyyzq8xajuv5ufaewzcdheuexfxmeceh3f0g"

# Generate a second seed phrase (e.g. https://pypi.org/project/mnemonic/)
SEED_PHRASE = "put_your_xxxrr"

# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

# Then go to https://agentverse.ai to get your API key and register a second agent
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYXBpLWtleSIsIm5vbmNlIjoiZmViZjY1NzAtZTQ0Yy00NjNjLTg4ZDctZmIzMWQwODQ2NzA1Iiwic3ViIjoiNWYxYTE5MGNlMThjZGU2YzJiM2UzMjlmZWEzZWQ1MmIxYTI0MzVjNzY2YWQyMWI5IiwiZXhwIjoxNzA1NDk3NjM2fQ.W4NAtp84O2ernWr0Y3t4yomm4vfqJFF1Y-09BD58UJY"

# Now your agent is ready to join the agentverse!
agent = Agent(
    name="bob",
    seed=SEED_PHRASE,
    mailbox=f"{API_KEY}@https://agentverse.ai",
)

fund_agent_if_low(agent.wallet.address())


@agent.on_interval(period=2.0)
async def send_message(ctx: Context):
    ctx.logger.info("Sending message to alice")
    await ctx.send(ALICE_ADDRESS, Message(message="hello there alice"))


@agent.on_message(model=Message, replies=set())
async def on_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    agent.run()
