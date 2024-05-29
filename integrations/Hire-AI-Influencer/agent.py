from uagents import Agent, Context, Protocol, Model
from uagents.setup import fund_agent_if_low

# third party modules used in this example
import uuid
import requests
from pydantic import BaseModel, Field
from ai_engine import UAgentResponse, UAgentResponseType

import stable

SEED_PHRASE = "Random seed"
# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")

AGENT_MAILBOX_KEY = "Generate your mailbox key"

agent = Agent(
    name="Hire AI influencer",
    port=6145,
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

fund_agent_if_low(agent.wallet.address())

@agent.on_event("startup")
async def hi(ctx: Context):
    ctx.logger.info(f"agnent address: {agent.address}")

class Stability(Model):
    prompt: str = Field(description="Text prompt of the image to be generated.")
    username: list[str] = Field(description='Option for Username. Must be "seema.ai.2024" or "lalit.ai.2024" ')


stability_protocol = Protocol("Stability_Protocol")

async def image_req(prompt: str, username : str):
    """
    Generates Image for a given Prompt using the Stability API.

    Args:
        prompt (str): Text prompt of the image to be generated.

    Returns:
        string or None: returns the link of the image if the image is generated correctly else returns None.
    """
    return stable.image_req(prompt,username)


@stability_protocol.on_message(model=Stability, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: Stability):
    ctx.logger.info(f"Received message from {sender}.")
    try:
        # Await the image_req coroutine
        result = await image_req(msg.prompt,msg.username)
        await ctx.send(
            sender, 
            UAgentResponse(message=str(result['link']), 
                           type=UAgentResponseType.FINAL)
        )
    except Exception as e:
        ctx.logger.info(f"Error generating response: {e}")
        # Send an error response back to the user

agent.include(stability_protocol,publish_manifest=True)

agent.run()
    
