from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low
from urllib.parse import urlparse
import requests

def download_image(image_url, save_path):
    response = requests.get(image_url)
    with open(save_path, "wb") as f:
        f.write(response.content)

def query(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    response = requests.post(API_URL, headers=HEADERS, data=data)
    return response.json()

class ImageData(Model):
    url: str

agent2 = Agent(
    name="agent2",
    seed="HUGGING_FACE_ACCESS_TOKEN1",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"],
)

fund_agent_if_low(agent2.wallet.address())
print(agent2.address)

# Initialize a flag to keep track of whether the message has been sent successfully
message_sent = False

@agent2.on_message(model=ImageData)
async def message_handler(ctx: Context, sender: str, msg: ImageData):
    global message_sent  # Declare the variable as global so it can be modified within the function
    ctx.logger.info(f"Received message from {sender}: {msg.url}")
    ctx.logger.info(f"got the image url ")
    image_path = urlparse(msg.url).path.split("/")[-1]  # Extract filename from URL
    download_image(msg.url, image_path)  # Download the image
    output = query(image_path)
    print(output)
    # client = Client("stabilityai/TripoSR")
    
   
    
    ctx.logger.info(f"doone image processing")
    

if __name__ == "__main__":
    agent2.run()
