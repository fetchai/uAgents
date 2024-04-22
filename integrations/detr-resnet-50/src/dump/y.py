import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from uagents import Agent, Context
from urllib.parse import urlparse

API_URL = "https://api-inference.huggingface.co/models/facebook/detr-resnet-50"
HEADERS = {"Authorization": "Bearer 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"}

def query(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    response = requests.post(API_URL, headers=HEADERS, data=data)
    return response.json()

def download_image(image_url, save_path):
    response = requests.get(image_url)
    with open(save_path, "wb") as f:
        f.write(response.content)

# Define and initialize the agent
alice = Agent(name="alice", port=8000, seed="alice secret phrase", endpoint=["http://127.0.0.1:8000/submit"])

# Define and register event handlers
@alice.on_event("startup")
async def say_hello(ctx: Context):
    ctx.storage.set("count", 0)
    ctx.storage.set("image_sent", False)
    ctx.logger.info(f'Hello, my name is {ctx.name}')

@alice.on_interval(period=2.0)
async def process_image(ctx: Context):
    image_sent = ctx.storage.get("image_sent")
    if not image_sent:
        image_path = ctx.storage.get("image_path")
        output = query(image_path)
        print(output)
        ctx.storage.set("image_sent", True)
        ctx.logger.info("Image sent for processing.")
    else:
        ctx.logger.info("Image already sent.")

def main():
    st.title("Image Processing App")
    
    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        if st.button("Process Image"):
            with st.spinner("Processing..."):
                image_path = "temp_image.png"
                image.save(image_path)
                alice.storage.set("image_path", image_path)
                alice.storage.set("image_sent", False)

if __name__ == "__main__":
    main()