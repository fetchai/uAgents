from uagents import Agent, Context, Protocol
from messages.bert_base import PredictionRequest, PredictionResponse, Error
from uagents.setup import fund_agent_if_low
import base64
import os
import pprint
import json

# masked sentence you want to predict
INPUT_TEXT = "The goal of life is [MASK]."

BERT_BASE_AGENT_ADDRESS = os.getenv(
    "BERT_BASE_AGENT_ADDRESS", "BERT_BASE_AGENT_ADDRESS")

if BERT_BASE_AGENT_ADDRESS == "BERT_BASE_AGENT_ADDRESS":
    raise Exception(
        "You need to provide an BERT_BASE_AGENT_ADDRESS, by exporting env, check README file")

# Define user agent with specified parameters
user = Agent(
    name="bert-base-uncased_user",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

# Check and top up the agent's fund if low
fund_agent_if_low(user.wallet.address())


@user.on_event("startup")
async def initialize_storage(ctx: Context):
    ctx.storage.set("PredictionDone", False)


# Create an instance of Protocol with a label "BERTBaseUncasedModelUser"
bert_base_user = Protocol(name="BERTBaseUncasedModelUser", version="0.0.1")


@bert_base_user.on_interval(period=30, messages=PredictionRequest)
async def predict(ctx: Context):
    predictionDone = ctx.storage.get("PredictionDone")

    if not predictionDone:
        await ctx.send(BERT_BASE_AGENT_ADDRESS, PredictionRequest(masked_text=INPUT_TEXT))


@bert_base_user.on_message(model=PredictionResponse)
async def handle_data(ctx: Context, sender: str, response: PredictionResponse):
    # ctx.logger.info(f"predictions:  {response.data}")
    pprint.pprint(response.data)
    ctx.storage.set("PredictionDone", True)


@bert_base_user.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    ctx.logger.info(f"Got error from uagent: {error}")

# publish_manifest will make the protocol details available on agentverse.
user.include(bert_base_user, publish_manifest=True)

# Initiate the task
if __name__ == "__main__":
    bert_base_user.run()
