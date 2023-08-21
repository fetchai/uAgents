from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low


class Message(Model):
    message: str


# Copy ALICE_ADDRESS generated in alice.py
ALICE_ADDRESS = "paste_alice_address_here"

# Generate a second seed phrase (e.g. https://pypi.org/project/mnemonic/)
SEED_PHRASE = "put_your_seed_phrase_here"

# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

# Then go to https://agentverse.ai to get your API key and register a second agent
API_KEY = "put_your_API_key_here"

# Now your agent is ready to join the agentverse!
agent = Agent(
    name="bob",
    seed=SEED_PHRASE,
    mailbox=f"{API_KEY}@wss://agentverse.ai",
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
