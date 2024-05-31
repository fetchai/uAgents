from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
import os
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

# Extend your protocol with DallE image generation
class DallERequest(Model):
    image_description: str = Field(description="Give detailed description of the image you want to generate using DallE.")

SEED_PHRASE = "DallE Agent Secret Phrase"

# Create an agent with the seed phrase
agent = Agent(seed=SEED_PHRASE)

# Print the agent's address
print(f"Your agent's address is: {agent.address}")

AGENT_MAILBOX_KEY = "YOUR_MAILBOX_ID_HERE"

# Initialize the DallE agent
dallEAgent = Agent(
    name="DallE Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

# Define the protocol for DallE image generation
dallE_protocol = Protocol("DallE Protocol")

# Set the OpenAI API key
OPENAI_API_KEY = "YOUR_OPEN_API_KEY"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

@dallE_protocol.on_message(model=DallERequest, replies={UAgentResponse})
async def load_dalle(ctx: Context, sender: str, msg: DallERequest):
    dalle_wrapper = DallEAPIWrapper()
    ctx.logger.info(msg.image_description)
    image_prompt = msg.image_description
    
    # Generate the image and get the URL
    try:
        image_url = dalle_wrapper.run(image_prompt)
        html_link = f'<a href="{image_url}" target="_blank">Click here to view the generated image</a>'
    except Exception as e:
        ctx.logger.info(f"Error generating image: {e}")
        html_link = "Error generating image. Please try again later."
    
    # Send the response back to the user
    await ctx.send(
        sender, UAgentResponse(message=html_link, type=UAgentResponseType.FINAL)
    )

# Include the protocol in the agent
dallEAgent.include(dallE_protocol, publish_manifest=True)

# Run the agent
dallEAgent.run()


