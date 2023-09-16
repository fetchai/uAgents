# Import all necessary modules and resources from various libraries
from uagents import Agent, Context, Protocol
from messages.basic import CaptionRequest, CaptionResponse, Error
from uagents.setup import fund_agent_if_low
import os
import requests
import base64

# Get the HUGGING_FACE_ACCESS_TOKEN from environment variable or default to a placeholder string if not found.
HUGGING_FACE_ACCESS_TOKEN = os.getenv(
    "HUGGING_FACE_ACCESS_TOKEN", "HUGGING FACE secret phrase :)")

BLIP_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"

# Define headers for HTTP request, including content type and authorization details
HEADERS = {
    "Authorization": f"Bearer {HUGGING_FACE_ACCESS_TOKEN}"
}

# Create an agent with predefined properties
agent = Agent(
    name="blip_agent",
    seed=HUGGING_FACE_ACCESS_TOKEN,
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

# Ensure the agent has enough funds
fund_agent_if_low(agent.wallet.address())


# decodes the base64 string into an image, sends a POST request to the BLIP_URL containing the image data,
# and returns the response from the model as a JSON object. If an error occurs during the process,
# the function will inform the user about the specific error that occurred.
async def get_image_caption(ctx: Context, sender: str, imagedata: str):
    try:
        # Encoding the image data from ASCII to bytes
        imagedata = imagedata.encode("ascii")
        # Converting the image data from base64 to bytes
        imageBytes = base64.b64decode(imagedata)

        # Sending POST request to BLIP_URL with image bytes
        response = requests.post(BLIP_URL, headers=HEADERS, data=imageBytes)

        # If the request response is not successful (non-200 code), send error message
        if response.status_code != 200:
            await ctx.send(sender, Error(error=f"Error: {response.json().get('error')}"))
            return

        # Parse the first message (image caption) from the response
        message = response.json()[0]
        # Send the parsed response back to the sender/user
        await ctx.send(sender, CaptionResponse.parse_obj(message))
        return

    # If an unknown exception occurs, send a generic error message to the sender/user
    except Exception as ex:
        await ctx.send(sender, Error(error=f"Sorry, I wasn't able to complete your request this time. Error detail: {ex}"))
        return

# Create an instance of Protocol with a label "BlipImageCaptioning"
blip_agent = Protocol(name="BlipImageCaptioning", version="0.1.0")


@blip_agent.on_message(model=CaptionRequest, replies={CaptionResponse, Error})
async def handle_request(ctx: Context, sender: str, request: CaptionRequest):
    # Log the request details
    ctx.logger.info(f"Got request from  {sender}")

    # Get the image caption from blip model
    await get_image_caption(ctx, sender, request.image_data)


# Include the protocol with the agent, publish_manifest will make the protocol details available on Agentverse.
agent.include(blip_agent, publish_manifest=True)

# Define the main entry point of the application
if __name__ == "__main__":
    blip_agent.run()
