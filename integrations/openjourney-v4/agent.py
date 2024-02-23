
import requests
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/prompthero/openjourney-v4"
headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}
FIREBASE_API_URL = f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o"
API_KEY_PARAM = f"key={FIREBASE_API_KEY}"

class TextToImage(Model):
    """
    Describes the input payload for converting text to an image.
    """
    text: str = Field(description="Text to convert to an image.")

def upload_to_firebase_storage(image_data, destination_path):
    """
    Uploads image data to Firebase Storage.
    Args:
        image_data (bytes): Image data to be uploaded.
        destination_path (str): Path where the image will be stored.
    Returns:
        str: Firebase URL of the uploaded image.
    """
    upload_url = f"{FIREBASE_API_URL}/{destination_path}?{API_KEY_PARAM}"
    headers = {"Content-Type": "image/png"}

    response = requests.post(upload_url, headers=headers, data=image_data)

    if response.status_code == 200:
        download_url = response.json().get("downloadTokens", "")
        firebase_url = f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o/{destination_path}?alt=media&token={download_url}"
        return firebase_url
    else:
        print("Error uploading to Firebase Storage:", response.content)
        return None

def query(payload):
    """
    Queries the Hugging Face API to convert text to an image.
    Args:
        payload (dict): Input payload for the Hugging Face API.
    Returns:
        bytes: Image data.
    """
    try:
        response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload, timeout=40)
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error from Hugging Face API: {e}")
        return None

hugging_face_protocol = Protocol("Text to Image")

@hugging_face_protocol.on_message(model=TextToImage, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: TextToImage):
    """
    Handles incoming messages for converting text to an image.
    Args:
        ctx (Context): Context object for handling messages.
        sender (str): Sender's identifier.
        msg (TextToImage): Input message containing text to be converted.
    Returns:
        None
    """
    url = ""
    payload = {
        "inputs": msg.text
    }
    image_data = query(payload)
    if image_data:
        url = upload_to_firebase_storage(image_data, "images")
        seg = f"Here's the image url\n <a href={url}>{url}</a>"
        await ctx.send(sender, UAgentResponse(message=seg, type=UAgentResponseType.FINAL))
    await ctx.send(sender, UAgentResponse(message="No Image Found !", type=UAgentResponseType.FINAL))

agent.include(hugging_face_protocol)