import requests
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

APY_ACCESS_TOKEN = os.environ.get("APY_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")

WEBSUMMARISER_API_BASE_URL = "https://api.apyhub.com/extract/text/webpage?url="
WEBSUMMARISER_HEADERS = {"apy-token": f"{APY_ACCESS_TOKEN}"}
FIREBASE_API_URL = (
    f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o"
)
API_KEY_PARAM = f"key={FIREBASE_API_KEY}"


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


def get_website_description(websiteUrl):
    response = requests.get(
        WEBSUMMARISER_API_BASE_URL + websiteUrl, headers=WEBSUMMARISER_HEADERS
    )
    if response.status_code == 200:
        data = response.json()
        return data["data"]
    return ""


async def chat_with_gemini(message):
    genai.configure(api_key=f"{GEMINI_API_KEY}")
    model = genai.GenerativeModel("gemini-pro")
    chat = model.start_chat(history=[])
    while True:
        user_message = message
        if user_message.lower() == "quit":
            return "Exiting chat session."
        response = chat.send_message(user_message, stream=False)
        message = str(response.candidates[0].content.parts[0])
        data = json.loads(str(message[13:-7]).replace("\\n", "").replace("\\", "")[1:])
        return data


async def fetchReelsData(ctx, websiteUrl):
    data = ctx.storage.get(websiteUrl)
    if data is None:
        data = get_website_description(websiteUrl)
        if data is not None:
            ctx.storage.set(websiteUrl, data)
    reelsAndPostsData = ctx.storage.get("gemini-" + websiteUrl)
    if reelsAndPostsData is None:
        reelsAndPostsData = await chat_with_gemini(
            "I want to create 1 reels and 5 illustrated Instagram posts for my company with website "
            + websiteUrl
            + ". Can you go through this description of my company and write a description of 3 different reels and also give very detailed description of images to post along with a great professional caption with min 15 words. Also, make sure that the image in the post is not from the company product, as we have to feed this description to another service that generates the image form this image description. Also make sure image is a illustration and easy to produce.Please give this data in JSON string format which is convertable into python dict. Each reels should have minimum 7 scenes in it with background image described and text overlay given. Take this as a format of json in reels give array of scenes in which each scene has 2 indexs background_image and text_overlay, in posts give 2 indexes caption and detailed description of image to post.  \n\n"
            + data
        )
        if reelsAndPostsData is not None:
            ctx.storage.set("gemini-" + websiteUrl, json.dumps(reelsAndPostsData))
    else:
        reelsAndPostsData = json.loads(reelsAndPostsData)
    return reelsAndPostsData
