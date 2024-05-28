# Import all necessary modules and resources from various libraries
from uagents import Agent, Context, Protocol
from messages.basic import SDResponse, SDRequest, Error
from uagents.setup import fund_agent_if_low
import os
import shutil
import requests
import datetime

# Get the HUGGING_FACE_ACCESS_TOKEN from environment variable or default to a placeholder string if not found.
HUGGING_FACE_ACCESS_TOKEN = os.getenv(
    "HUGGING_FACE_ACCESS_TOKEN", "HUGGING FACE secret phrase :)")

# Define configurations used for HTTP requests to Hugging Face
STABLE_DIFFUSION_URL = "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"

# Define headers for HTTP request, including content type and authorization details
HEADERS = {"Content-Type": "application/json",
           "Authorization": f"Bearer {HUGGING_FACE_ACCESS_TOKEN}"}

# Create an agent with predefined properties
agent = Agent(name="stable_diffusion_agent", seed=HUGGING_FACE_ACCESS_TOKEN,
              port=8001, endpoint=["http://127.0.0.1:8001/submit"])

# Ensure the agent has enough funds
fund_agent_if_low(agent.wallet.address())

# Function to handle image request and save the image response


async def get_image(ctx: Context, sender: str, image_desc: str):
    # Prepare the data for HTTP request
    data = {"inputs": image_desc}
    # Define path where the image will be saved
    new_file_loc = os.path.join(os.getcwd(), "generated-image/" +
                                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ".jpeg")
    # Make the HTTP request and handle possible errors
    try:
        response = requests.post(STABLE_DIFFUSION_URL,
                                 headers=HEADERS, json=data, stream=True)
        if response.status_code == 200:
            with open(new_file_loc, 'wb') as out_file:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, out_file)
            await ctx.send(sender, SDResponse(image_data=f"file saved at location: {new_file_loc}"))
            return
        else:
            await ctx.send(sender, Error(error=f"Error: {response.content}"))
            return
    except Exception as ex:
        await ctx.send(sender, Error(error=f"Sorry, I wasn't able to answer your request this time. Feel free to try again. Error detail: {ex}"))
        return

# Create a protocol named "Request"
stable_diffusion_agent = Protocol("Request")

# Define a message handling function to manage incoming requests


@stable_diffusion_agent.on_message(model=SDRequest, replies={SDResponse})
async def handle_request(ctx: Context, sender: str, request: SDRequest):
    # Log the request details
    ctx.logger.info(
        f"Got request from  {sender} to auto complete this: {request.image_desc}")
    # Get the response from model
    await get_image(ctx, sender, request.image_desc)

# Include the protocol with the agent
agent.include(stable_diffusion_agent)

# Define the main entry point of the application
if __name__ == "__main__":
    stable_diffusion_agent.run()
