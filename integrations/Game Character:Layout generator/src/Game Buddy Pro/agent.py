import random
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType


def upload_to_imgur(image_bytes):
    # Endpoint for uploading images to Imgur
    imgur_upload_url = "https://api.imgur.com/3/upload"
    # Your Imgur client ID
    client_id = "4bcbf53406ad289"

    # Prepare headers with client ID
    headers = {"Authorization": f"Client-ID {client_id}"}

    # Prepare data with image binary
    files = {"image": image_bytes}

    # Send POST request to Imgur API
    response = requests.post(imgur_upload_url, headers=headers, files=files)

    # Parse the response JSON
    response_data = response.json()

    # Check if upload was successful
    if response_data["success"]:
        # Get the URL of the uploaded image
        image_url = response_data["data"]["link"]
        print(image_url)
        return image_url
    else:
        # Print error message if upload failed
        print("Error uploading image to Imgur:", response_data["data"]["error"])


class Character(Model):
    description: str = Field(description="Describe a character.")


character_protocol = Protocol("Character")


@character_protocol.on_message(model=Character, replies={UAgentResponse})
async def generate_character(ctx: Context, sender: str, msg: Character):
    API_URL = "https://api-inference.huggingface.co/models/veryVANYA/ps1-graphics-sdxl-v2"
    headers = {"Authorization": f"Bearer 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"}

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.content

    print(msg.description)
    image_bytes = query({
        "inputs": msg.description,
    })

    url = upload_to_imgur(image_bytes)

    final_url  = "<a href = "+url+">Tap to open image</a>"

    message = "Below is the link of image generated using the details provided by you: \n" + final_url + "\n " + "<img src="+url+"></img>"

    await ctx.send(
        sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL)
)
agent.include(character_protocol, publish_manifest=True)
