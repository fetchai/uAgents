# Import necessary agent-related modules
from uagents import Agent, Context, Protocol

# Import basic communication messages
from messages.basic import SDResponse, SDRequest, Error

# Import utility function for managing agent funds
from uagents.setup import fund_agent_if_low

# IMAGE_DESC will contain a brief description of the image that needs to be identified by AI
IMAGE_DESC = "Cats playing soccer"

# The address of the AI Model Agent in the network
AI_MODEL_AGENT_ADDRESS = "agent1q2gdm20yg3krr0k5nt8kf794ftm46x2cs7xyrm2gqc9ga5lulz9xsp4l4kk"

# Create a user agent with a specific name, port, and endpoint
user = Agent(
    name="stable_diffusion_user",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
)

# Checks and tops up the agent's funds if they are low
fund_agent_if_low(user.wallet.address())

# Create a protocol named "Request"
stable_diffusion_user = Protocol("Request")

# Define a timed function that will send a completion request to AI model agent every 360s


@stable_diffusion_user.on_interval(360, messages=SDRequest)
async def auto_complete(ctx: Context):
    ctx.logger.info(f"Asking AI model agent to complete this: {IMAGE_DESC}")
    await ctx.send(AI_MODEL_AGENT_ADDRESS, SDRequest(image_desc=IMAGE_DESC))

# Define a message handling function to manage responses from the AI model agent


@stable_diffusion_user.on_message(model=SDResponse)
async def handle_data(ctx: Context, sender: str, data: SDResponse):
    ctx.logger.info(f"Got response from Agent: {data.image_data}")

# Define a message handling function to manage errors from the AI model agent


@stable_diffusion_user.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    ctx.logger.info(f"Got error from AI model agent: {error}")

# Include the Protocol to the agent's available protocols
user.include(stable_diffusion_user)

# Run main loop if file runs as the primary module
if __name__ == "__main__":
    stable_diffusion_user.run()
