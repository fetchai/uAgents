import requests
from reel_creation_proto import UAgentResponse, UAgentResponseType, reel_creation_proto
from uagents import Agent, Context, Protocol, Model
import os
import time
from dotenv import load_dotenv
from utils import fetchReelsData

load_dotenv()

post_creation_protocol = Protocol("PostCreation")
SEED_PHRASE = os.environ.get("SEED_PHRASE")
APY_ACCESS_TOKEN = os.environ.get("APY_ACCESS_TOKEN")
IMAGE_CREATION_API_TOKEN = os.environ.get("IMAGE_CREATION_API_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
AGENT_MAILBOX_KEY = os.environ.get("AGENT_MAILBOX_KEY")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")

WEBSUMMARISER_API_BASE_URL = "https://api.apyhub.com/extract/text/webpage?url="
WEBSUMMARISER_HEADERS = {"apy-token": f"{APY_ACCESS_TOKEN}"}
IMAGE_CREATION_API_URL = (
    "https://api-inference.huggingface.co/models/stablediffusionapi/crystal-clear-xlv1"
)
IMAGE_CREATION_HEADERS = {"Authorization": f"Bearer {IMAGE_CREATION_API_TOKEN}"}
FIREBASE_API_URL = (
    f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o"
)
API_KEY_PARAM = f"key={FIREBASE_API_KEY}"

print(f"Your agent's address is: {Agent(seed=SEED_PHRASE).address}")
localagent = Agent(
    name="Local Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)


async def uploadToFirebaseStorage(file_data, destination_path, fileType):
    upload_url = f"{FIREBASE_API_URL}/{destination_path}?{API_KEY_PARAM}"
    contentType = "image/png"
    if fileType == "video":
        contentType = "video/mp4"
    headers = {"Content-Type": f"{contentType}"}
    print(upload_url)
    response = requests.post(upload_url, headers=headers, data=file_data)

    if response.status_code == 200:
        download_url = response.json().get("downloadTokens", "")
        firebase_url = (
            f"{FIREBASE_API_URL}/{destination_path}?alt=media&token={download_url}"
        )
        print(download_url)
        return firebase_url
    else:
        print("Error uploading to Firebase Storage:", response.content)
        return None


async def createImageFromText(message, website):
    response = requests.post(
        IMAGE_CREATION_API_URL,
        headers=IMAGE_CREATION_HEADERS,
        json={"inputs": str(message)},
    )
    website = website.replace("://", "").replace(".", "").replace("/", "_")
    fileName = website + "(())" + str(time.time()).replace(".", "")
    url = await uploadToFirebaseStorage(response.content, f"{fileName}.png", "image")
    return url


class PostCreation(Model):
    websiteUrl: str


@post_creation_protocol.on_message(model=PostCreation, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: PostCreation):
    ctx.logger.info(f"Received message from {sender}.")

    try:
        reelsAndPostsData = await fetchReelsData(ctx, msg.websiteUrl)
        final_message = "Hello we have created a few posts from your website for you. Please have a look at them.\n\n"
        post = 1
        for item in reelsAndPostsData["posts"]:
            nonCaptionTerm = list(filter(lambda x: x != "caption", item.keys()))[0]
            # print(nonCaptionTerm)
            url = await createImageFromText(item[nonCaptionTerm], msg.websiteUrl)
            final_message += f"\nPost {post}\n"
            final_message += (
                f'Image Link - <a href="{url}" target="_blank">Open Image</a>\n'
            )
            final_message += "Caption - " + item["caption"] + "\n"
            post = post + 1
        await ctx.send(
            sender, UAgentResponse(message=final_message, type=UAgentResponseType.FINAL)
        )

    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR)
        )


localagent.include(post_creation_protocol)
localagent.include(reel_creation_proto)
localagent.run()
