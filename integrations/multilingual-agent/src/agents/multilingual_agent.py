# Necessary imports: uagents for agent creation and message handling,
# os and requests for managing API calls
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
from messages.basic import UAResponse, UARequest, Error
from uagents.setup import fund_agent_if_low
import os
import requests
from utils.functions import get_video_script, summarize_transcript

# The access token and URL for the SAMSUM BART model, served by Hugging Face
HUGGING_FACE_ACCESS_TOKEN = os.getenv(
    "HUGGING_FACE_ACCESS_TOKEN", "HUGGING FACE secret phrase :)")
SAMSUM_BART_URL = "https://api-inference.huggingface.co/models/Samuela39/my-samsum-model"

# Setting the headers for the API call
HEADERS = {
    "Authorization": f"Bearer {HUGGING_FACE_ACCESS_TOKEN}"
}

SEED=HUGGING_FACE_ACCESS_TOKEN


# Copy the address shown below
print(f"Your agent's address is: {Agent(seed=SEED).address}")


# Then go to https://agentverse.ai, register your agent in the Mailroom
# and copy the agent's mailbox key
AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY", None)
assert (
    AGENT_MAILBOX_KEY is not None
), "AGENT_MAILBOX_KEY environment variable is not set! Please set it to your agent's mailbox key!"

# Now your agent is ready to join the agentverse!
agent = Agent(
    name="multilingual-agent",
    seed=SEED,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

# # Creating the agent and funding it if necessary
# agent = Agent(
#     name="multilingual-agent",
#     seed=SEED,
#     port=8001,
#     endpoint=["http://127.0.0.1:8001/submit"],
# )
# fund_agent_if_low(agent.wallet.address())

class UAResponse(Model):
    response: list

class SummarizationRequest(Model):
    url: str = Field(description="URL of the video you want to summarize")

# Protocol declaration for UARequests
multilingual_agent = Protocol("summary-request","0.1.0")

# Declaration of a message event handler for handling UARequests and send respective response.
@multilingual_agent.on_message(model=SummarizationRequest, replies={UAResponse, Error})
async def handle_request(ctx: Context, sender: str, msg: SummarizationRequest):
    # Logging the request information
    ctx.logger.info(
        f"Got request from  {sender} for summarization : {msg.url}")
    
    try:
        transcript = get_video_script(msg.video_link)
    except Exception as e:
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"No transcript found for video! Error: {e}",
                type=UAgentResponseType.ERROR,
            ),
        )
        return

    summary = await summarize_transcript(transcript, msg.model)

    print("Sending short article")
    await ctx.send(
        sender,
        UAgentResponse(
            message=f"Summary:\n{summary}",
            type=UAgentResponseType.FINAL,
        ),
    )
    return


# Include protocol to the agent
agent.include(multilingual_agent, publish_manifest=True)

if __name__ == "__main__":
    agent.run()