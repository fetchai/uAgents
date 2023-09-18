from uagents import Agent, Context, Protocol  # Import necessary modules
# Import Basic messages
from messages.basic import CaptionRequest, CaptionResponse, Error

# Import the fund_agent_if_low function
from uagents.setup import fund_agent_if_low

import base64

IMAGE_FILE = "sample-images/gandhi.jpg"

# AI model agent address
AI_MODEL_AGENT_ADDRESS = "agent1q2gdm20yg3krr0k5nt8kf794ftm46x2cs7xyrm2gqc9ga5lulz9xsp4l4kk"

# Define user agent with specified parameters
user = Agent(
    name="blip_user",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
)

# Check and top up the agent's fund if low
fund_agent_if_low(user.wallet.address())


@user.on_event("startup")
async def initialize_storage(ctx: Context):
    ctx.storage.set("captionCreated", False)


# Create an instance of Protocol with a label "BlipImageCaptioningUser"
blip_user = Protocol(name="BlipImageCaptioningUser", version="0.1.0")


# This is an asynchronous function that is set to run at intervals of 30 sec.
# It opens the specified IMAGE_FILE, reads it and encodes the image in base64 format.
# Afterwards, it sends a request with the encoded data to the AI uagent's address.
@blip_user.on_interval(period=30, messages=CaptionRequest)
async def image_caption(ctx: Context):
    captionCreated = ctx.storage.get("captionCreated")

    if not captionCreated:
        # Opening the file in read binary mode
        with open(IMAGE_FILE, "rb") as f:
            # Encoding the image data to base64
            data = base64.b64encode(f.read()).decode('ascii')
        # Using the context to send the request to the desired address with the image data
        await ctx.send(AI_MODEL_AGENT_ADDRESS, CaptionRequest(image_data=data))


# Define a function to handle and
# log data received from the AI model agent
@blip_user.on_message(model=CaptionResponse)
async def handle_data(ctx: Context, sender: str, caption: CaptionResponse):
    ctx.logger.info(f"image caption => {caption.generated_text}")
    ctx.storage.set("captionCreated", True)

# Define a function to handle and log errors occurred during process


@blip_user.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    ctx.logger.info(f"Got error from uagent: {error}")

# Include the protocol with the agent, publish_manifest will make the protocol details available on Agentverse.
user.include(blip_user, publish_manifest=True)

# Initiate the image captioning task
if __name__ == "__main__":
    blip_user.run()
