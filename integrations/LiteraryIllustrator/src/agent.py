import requests
from pydantic import BaseModel, Field
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol, Model

# Define the API keys and URLs
BERT_API_URL = "https://api-inference.huggingface.co/models/google-bert/bert-base-uncased"
BERT_HEADERS = {"Authorization": "Bearer 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"}

STADIF_API_KEY = "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"

# Define the models for prompt generation and image generation
class PromptGenModel(Model):
    paragraph: str = Field(description="Given a paragraph prompt describing a scene or concept, your task is to identify and extract useful and relevant information or tokens that can be utilized for image generation. Focus on key details such as objects, settings, actions, emotions, and any other elements that contribute to the visual representation of the described scene. Your output should provide a structured representation of the extracted information, facilitating the generation of coherent and visually compelling images. Please ensure that the extracted tokens accurately reflect the content and context of the paragraph prompt. Ignore all other irrelevant information")

class ImgGenModel(Model):
    symbol: str = Field(description="Enter prompt to generate high quality, realistic images with dynamic lighting that envoke strong emotions in a visually appealing and interesting way")

# Function to query BERT model for relevant information extraction
def query_bert(paragraph: str):
    try:
        response = requests.post(BERT_API_URL, headers=BERT_HEADERS, json={"inputs": paragraph})
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error from Hugging Face API: {e}")

# Function to query image generation model
def query_img_gen(symbol: str):
    API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    headers = {"Authorization": f"Bearer {STADIF_API_KEY}"}
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": symbol})
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.content
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error from Hugging Face API: {e}")

# Function to upload image to Imgur
def upload_image_to_imgur(image_bytes):
    headers = {
        "Authorization": "Client-ID ff9ffff4455eadf"  # Replace "your-client-id" with your actual Imgur client ID
    }
    files = {
        'image': ('generated_image.jpg', image_bytes, 'image/jpeg')
    }
    try:
        response = requests.post("https://api.imgur.com/3/image", headers=headers, files=files)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()["data"]["link"]
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error uploading image to Imgur: {e}")

# Define protocols for handling prompt generation and image generation
PromptGen_protocol = Protocol("PromptGenProtocol")
ImgGen_protocol = Protocol("ImgGenProtocol")

# Function to handle prompt generation
@PromptGen_protocol.on_message(model=PromptGenModel, replies={ImgGenModel})
def handle_promptgen(ctx: Context, sender: str, msg: PromptGenModel):
    ctx.logger.info(f"Received message from {sender}, session: {ctx.session}")
    try:
        relevant_info = query_bert(msg.paragraph)
        ctx.logger.info(f"Relevant information extracted: {relevant_info}")
        ctx.send(sender, ImgGenModel(symbol=relevant_info))
    except Exception as ex:
        ctx.logger.error(f"Error occurred during relevant information extraction: {ex}")
        ctx.send(sender, UAgentResponse(message=str(ex), type=UAgentResponseType.ERROR))

# Function to handle image generation
@ImgGen_protocol.on_message(model=ImgGenModel, replies={UAgentResponse})
def handle_imggen(ctx: Context, sender: str, msg: ImgGenModel):
    ctx.logger.info(f"Received message from {sender}, session: {ctx.session}")
    try:
        image_bytes = query_img_gen(msg.symbol)
        image_link = upload_image_to_imgur(image_bytes)
        ctx.logger.info(f"Image link from Imgur: {image_link}")
        ctx.send(sender, UAgentResponse(message=image_link, type=UAgentResponseType.FINAL))
    except Exception as ex:
        ctx.logger.error(f"Error occurred during image generation: {ex}")
        ctx.send(sender, UAgentResponse(message=str(ex), type=UAgentResponseType.ERROR))

# Initialize the agent
agent = Agent()

# Include ImgGen_protocol
agent.include(ImgGen_protocol, publish_manifest=True)

# Include PromptGen_protocol if ImgGen_protocol is successfully included
if ImgGen_protocol in agent.protocols:
    agent.include(PromptGen_protocol, publish_manifest=True)
