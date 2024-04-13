# Import necessary modules
from uagents import Agent, Context, Protocol, Model, Bureau
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
import requests
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Retrieve necessary API keys from environment variables
AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")
IMG_BB_API_KEY = os.getenv("IMG_BB_KEY")
HUGGING_FACE_KEY = os.getenv("HUGGING_FACE_KEY")

# Define the API URLs for the Hugging Face model and ImgBB
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
IMG_BB_API_URL = "https://api.imgbb.com/1/upload"

# Configure headers for the Hugging Face API request
headers = {"Authorization": f"Bearer {HUGGING_FACE_KEY}"}

# Define the GetImage agent
GetImage = Agent(
    name="GetImage",
    seed="alice recovery phrase",
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

# Function to query the Hugging Face API
def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content

# Function to upload an image to ImgBB and return its URL
def upload_image_to_imgbb(image_bytes):
    response = requests.post(
        IMG_BB_API_URL,
        files={'image': image_bytes},
        data={'key': IMG_BB_API_KEY}
    )
    return response.json()['data']['url']

# Define the GetImage model using Pydantic for data validation
class GetImage(Model):
    prompt: str = Field(description="the prompt which is used to create the image identify it from the user")

# Define the communication protocol
Get_Image_protocol = Protocol("GetImage")

# Define the message handling function for the GetImage protocol
@Get_Image_protocol.on_message(model=GetImage, replies={UAgentResponse})
async def Get_image(ctx: Context, sender: str, msg: GetImage):
    # Generate image in normal style
    image_bytes_normal = query({"inputs": f"{msg.prompt} in normal style",})
    image_url_normal = upload_image_to_imgbb(image_bytes_normal)

    # Generate image in vintage style
    image_bytes_vintage = query({"inputs": f"{msg.prompt} in vintage style",})
    image_url_vintage = upload_image_to_imgbb(image_bytes_vintage)

    # Generate image as a painting
    image_bytes_Painting = query({"inputs": f"{msg.prompt} in Painting",})
    image_url_Painting = upload_image_to_imgbb(image_bytes_Painting)

    # Generate image in animation style
    image_bytes_Animation = query({"inputs": f"{msg.prompt} in Animation style",})
    image_url_Animation = upload_image_to_imgbb(image_bytes_Animation)

    # Compose message with links to the generated images
    mssg = f"your style link:<a href={image_url_normal}> Image Link </a>\n"
    mssg += f"vintage style link:<a href={image_url_vintage}> Image Link </a>\n"
    mssg += f"painting link:<a href={image_url_Painting}> Image Link </a>\n"
    mssg += f"animation link:<a href={image_url_Animation}> Image Link </a>\n"

    # Send the message as a response to the sender
    await ctx.send(
        sender, UAgentResponse(message=mssg, type=UAgentResponseType.FINAL)
    )

# Include the protocol in the GetImage model and publish its manifest
GetImage.include(Get_Image_protocol, publish_manifest=True)

# Run the GetImage agent
GetImage.run()
