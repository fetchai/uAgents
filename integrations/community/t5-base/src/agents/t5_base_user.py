from uagents import Agent, Context, Protocol
from messages.t5_base import TranslationRequest, TranslationResponse, Error
from uagents.setup import fund_agent_if_low
import base64
import os

# text you want to translate
INPUT_TEXT = "Who are you?"

T5_BASE_AGENT_ADDRESS = os.getenv(
    "T5_BASE_AGENT_ADDRESS", "T5_BASE_AGENT_ADDRESS")

if T5_BASE_AGENT_ADDRESS == "T5_BASE_AGENT_ADDRESS":
    raise Exception(
        "You need to provide an T5_BASE_AGENT_ADDRESS, by exporting env, check README file")

# Define user agent with specified parameters
user = Agent(
    name="t5_base_user",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

# Check and top up the agent's fund if low
fund_agent_if_low(user.wallet.address())


@user.on_event("startup")
async def initialize_storage(ctx: Context):
    ctx.storage.set("TranslationDone", False)


# Create an instance of Protocol with a label "T5BaseModelUser"
t5_base_user = Protocol(name="T5BaseModelUser", version="0.0.1")


@t5_base_user.on_interval(period=30, messages=TranslationRequest)
async def transcript(ctx: Context):
    TranslationDone = ctx.storage.get("TranslationDone")

    if not TranslationDone:
        await ctx.send(T5_BASE_AGENT_ADDRESS, TranslationRequest(text=INPUT_TEXT))


@t5_base_user.on_message(model=TranslationResponse)
async def handle_data(ctx: Context, sender: str, response: TranslationResponse):
    ctx.logger.info(f"Translated text:  {response.translated_text}")
    ctx.storage.set("TranslationDone", True)


@t5_base_user.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    ctx.logger.info(f"Got error from uagent: {error}")

# publish_manifest will make the protocol details available on agentverse.
user.include(t5_base_user, publish_manifest=True)

# Initiate the task
if __name__ == "__main__":
    t5_base_user.run()
