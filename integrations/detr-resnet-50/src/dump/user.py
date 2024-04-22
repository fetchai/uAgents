from uagents import Agent, Context, Protocol,Model
from uagents.setup import fund_agent_if_low
from gradio_client import Client

import requests
from PIL import Image
from io import BytesIO


API_URL = "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png"

RECIPIENT_ADDRESS="agent1q2syczlapez5qq4qlueqfhlqn90er3qvn2gkjw3m7954j0ykqjuvxmu0fma"

user = Agent(
    name="agent1",
    seed="HUGGING_FACE_ACCESS_TOKEN",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)


class ImageData(Model):
    url: str

fund_agent_if_low(user.wallet.address())




@user.on_event("startup")
async def send_message(ctx: Context):
    ctx.logger.info(f"sending message to agent2")
    data="https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png"
    await ctx.send(RECIPIENT_ADDRESS, ImageData(url=data))


if __name__ == "__main__":
    user.run()