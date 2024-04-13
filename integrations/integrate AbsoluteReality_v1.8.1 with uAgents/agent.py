import os
from dotenv import load_dotenv
from uagents import Agent, Context, Model
from pydantic import Field

class Message(Model):
    message: str

class Story(Model):
    text: str = Field(description="The story provided by the user.")

async def setup_agent():
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve environment variables
    ALICE_ADDRESS = os.getenv("ALICE_ADDRESS")
    BOB_ADDRESS = os.getenv("BOB_ADDRESS")
    SEED_PHRASE = os.getenv("SEED_PHRASE")
    AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")

    # Now your agent is ready to join the agentverse!
    agent = Agent(
        name="bob",
        seed=SEED_PHRASE,
        mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
    )

    @agent.on_interval(period=2.0)
    async def send_message(ctx: Context):
        ctx.logger.info("Sending message to alice")
        await ctx.send(ALICE_ADDRESS, Message(message="hello there alice"))

    @agent.on_message(model=Message, replies=set())
    async def on_message(ctx: Context, sender: str, msg: Message):
        ctx.logger.info(f"Received message from {sender}: {msg.message}")

    @agent.on_message(model=Story, replies=set())
    async def receive_story(ctx: Context, sender: str, msg: Story):
        ctx.logger.info(f"Received story from {sender}: {msg.text}")
        # Now send the received story to the other agent
        await ctx.send(BOB_ADDRESS, msg)

    @agent.on_message(model=Message)
    async def receive_response(ctx: Context, sender: str, msg: Message):
        ctx.logger.info(f"Received response from {sender}: {msg.message}")
        # Process the response as needed

    return agent

if __name__ == "__main__":
    # Set up the agent
    agent = setup_agent()

    # Run the agent
    agent.run()
