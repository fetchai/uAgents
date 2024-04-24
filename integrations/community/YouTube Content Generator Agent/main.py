
from uagents import Agent, Context, Protocol, Model, Bureau
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
import PIL  
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import os
import shutil
import requests
import datetime
from transformers import pipeline
import google.generativeai as genai
from elevenlabs import save,VoiceSettings,Voice
from elevenlabs.client import ElevenLabs
import time


class ImageGen(Model):
    prompt: str = Field(description="Enter the image Prompt")

#all the apikeys
load_dotenv()
AGENT_MAILBOX_KEY =os.getenv("AGENT_MAILBOX_KEY")
HUGGING_FACE_ACCESS_TOKEN = os.getenv("HUGGING_FACE_ACCESS_TOKEN")
genai.configure(api_key=os.getenv("gemini_api_key"))
client = ElevenLabs(
  api_key=os.getenv("elevenLabs_api_key"), # Defaults to ELEVEN_API_KEY
)
cloudinary.config( 
        cloud_name = os.getenv("cloudinary_cloud_name"), 
        api_key = os.getenv("cloudinary_api_key"), 
        api_secret = os.getenv("cloudinary_api_secret") 
    )


#Animagine-xl api hosted on hugging face
STABLE_DIFFUSION_URL = "https://api-inference.huggingface.co/models/stablediffusionapi/animagine-xl-31"


HEADERS = {"Content-Type": "application/json",
           "Authorization": f"Bearer {HUGGING_FACE_ACCESS_TOKEN}"}
SEED_PHRASE = "image caption gen"#this needs to be unique



ImageGenAgent=Agent(name="CaptionGenAgent",
                seed=SEED_PHRASE,
                mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)
summary_protocol = Protocol("Caption Generation")


# importing the image to text model
image_to_text =pipeline("image-to-text",model="Salesforce/blip-image-captioning-base")

#creates caption from image
def image2text(url):
    text=image_to_text(url)[0]['generated_text']
    print(text)
    return text

# creates story from a text
def StoryGen(text):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(f'write a story on the caption{text}')
    return response




@summary_protocol.on_message(model=ImageGen, replies={UAgentResponse})
async def summarize_news(ctx: Context, sender: str, msg: ImageGen):

    # logging the Agent Address
    ctx.logger.info(ImageGenAgent.address)

    #creating an image from the prompt
    image_desc =f"{msg.prompt}"
    data = {"inputs": image_desc}
    response = requests.post(STABLE_DIFFUSION_URL,
                            headers=HEADERS, json=data, stream=True)
    

    #saving the image to the local drive
    if response.status_code == 200:
        with open("img.jpg", 'wb') as out_file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, out_file)
    else:
        print("error")
    
    time.sleeo(5) #this is important for cloudinary to wait before a proper image file is generated
    #uploading the image to cloudinary and getting the url
    res=cloudinary.uploader.upload("img.jpg")
    url = res["url"]
    print(url)


    #creating a story from the image
    response=StoryGen(f'Write a story With proper title using the prompt : {msg.prompt}')
    print(f"Story:{response.text}")

    #converting that story into an audio file
    audio = client.generate(
    text=response.text,
    voice=Voice(
        voice_id=os.getenv("eleven_voice_id"),
        settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
        )
    )
    #saving the file to local storage
    save(audio,"my-file.mp3")
    #uploading the audio file to cloud
    upload_result = cloudinary.uploader.upload("my-file.mp3", resource_type="video")
    uploaded_file_url = upload_result["url"]

    await ctx.send(
        sender,
        UAgentResponse(message=(f"Image url:<a href={url}> Image Link </a> \n Story Generated:\n {response.text} \n <a href={uploaded_file_url}>  Audio link </a> "), type=UAgentResponseType.FINAL),
    )
    
    
ImageGenAgent.include(summary_protocol, publish_manifest=True)

ImageGenAgent.run()

