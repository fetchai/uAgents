import requests
from pydantic import BaseModel, Field
from ai_engine import UAgentResponse, UAgentResponseType

HUGGING_FACE_API_URL = "https://api-inference.huggingface.co/models/text2emoji"
headers = {"Authorization": f"Bearer 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"}

class TextToEmoji(BaseModel):
    """
    Describes the input payload for converting text to emojis.
    """
    text: str = Field(description="Text to convert to emojis.")

def query(payload):
    """
    Queries the Hugging Face API to convert text to emojis.
    Args:
        payload (dict): Input payload for the Hugging Face API.
    Returns:
        str: Emoji representation of the text.
    """
    try:
        response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload, timeout=40)
        if response.status_code == 200:
            return response.json().get("outputs")
        else:
            print("Error from Hugging Face API:", response.content)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error from Hugging Face API: {e}")
        return None

hugging_face_protocol = Protocol("Text to Emoji")

@hugging_face_protocol.on_message(model=TextToEmoji, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: TextToEmoji):
    """
    Handles incoming messages for converting text to emojis.
    Args:
        ctx (Context): Context object for handling messages.
        sender (str): Sender's identifier.
        msg (TextToEmoji): Input message containing text to be converted.
    Returns:
        None
    """
    # Hardcoded output for demonstration purposes
    output_emoji = "👋🌍!"

    await ctx.send(sender, UAgentResponse(message=output_emoji, type=UAgentResponseType.FINAL))

agent.include(hugging_face_protocol)


