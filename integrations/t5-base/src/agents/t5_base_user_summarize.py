from uagents import Agent, Context, Protocol
from messages.t5_base import SummarizationRequest, SummarizationResponse, Error
from uagents.setup import fund_agent_if_low
import base64
import os

# Replace this input with the text you want to summarize
INPUT_TEXT = """The study examines factors relevant to the projection of CCs (commitment contexts) and assesses their contributions to projection behavior. A model with predicate as a fixed effect shows the highest explanatory power, confirming theoretical claims about the role of embedding, genre, tense, person, and predicate lemma in projection. However, even with all factors considered, the model's Nagelkerke R2 remains at 0.35. Additional analyses incorporating plausibility means of CCs indicate more variability in the data to be accounted for, suggesting the need for further exploration. The CommitmentBank study emphasizes the complexity of understanding projectivity, highlighting the necessity for integrating multiple factors for a comprehensive account."""
# The example text given above is from section 3.5. Summary analyses of the paper https://semanticsarchive.net/Archive/Tg3ZGI2M/Marneffe.pdf used in citation for t5_base on huggingface https://huggingface.co/t5-base#uses. Replace it with your own text for summarization.

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
    ctx.storage.set("SummarizationDone", False)


# Create an instance of Protocol with a label "T5BaseModelUser"
t5_base_user = Protocol(name="T5BaseModelUser", version="0.0.1")


@t5_base_user.on_interval(period=30, messages=SummarizationRequest)
async def transcript(ctx: Context):
    SummarizationDone = ctx.storage.get("SummarizationDone")

    if not SummarizationDone:
        await ctx.send(T5_BASE_AGENT_ADDRESS, SummarizationRequest(text=f"summarize: {INPUT_TEXT}"))


@t5_base_user.on_message(model=SummarizationResponse)
async def handle_data(ctx: Context, sender: str, response: SummarizationResponse):
    ctx.logger.info(f"Summarized text:  {response.summarized_text}")
    ctx.storage.set("SummarizationDone", True)


@t5_base_user.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    ctx.logger.info(f"Got error from uagent: {error}")

# publish_manifest will make the protocol details available on agentverse.
user.include(t5_base_user, publish_manifest=True)

# Initiate the task
if __name__ == "__main__":
    t5_base_user.run()