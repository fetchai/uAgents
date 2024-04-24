import requests
import os
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
from serpapi import GoogleSearch

def get_concise_google_lens_info(image_url,api_key):
    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": api_key  # Replace with your actual API key
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    visual_matches = results.get("visual_matches", [])
    res_str = ""
    
    # Extracting information from the first three visual matches
    for i, match in enumerate(visual_matches[:3]):
        title = match.get('title', 'N/A')
        link = match.get('link', 'N/A')
        source = match.get('source', 'N/A')
        res_str += (
            f"Match {i + 1}:\n"
            f"Title: {title}\n"
            f"Link: <a href='{link}'>{title}</a>\n"
            f"Source: {source}\n\n"
        )
    
    return res_str if res_str else "No visual matches found."


# Define the request model for your business analysis
class GoogleLensRequest(Model):
    image_url: str = Field(description="Please provide image url for which you want to run google lens query? ")

# Initialize your agent
SEED_PHRASE = "Google Lens Seed Phrase"
AGENT_MAILBOX_KEY = "<your_agent_mailbox_address>"
googleLensAgent = Agent(
    name="Google Lens Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)
print(googleLensAgent.address)
# Fund the agent if needed
fund_agent_if_low(googleLensAgent.wallet.address())

# Define a protocol for handling business analysis requests
googleLensProtocol = Protocol("Google Lens Protocol")

# Define the behavior when a message is received
@googleLensProtocol.on_message(model=GoogleLensRequest, replies={UAgentResponse})
async def handle_business_analysis_request(ctx: Context, sender: str, msg: GoogleLensRequest):
    ctx.logger.info(f'User has requested details for {msg.image_url}')
    api_key = os.getenv('google_Lens_api_key')
    response = get_concise_google_lens_info(msg.image_url, api_key)
    ctx.logger.info(str(response))
    await ctx.send(sender, UAgentResponse(message=str(response), type=UAgentResponseType.FINAL))

# Start the agent
googleLensAgent.include(googleLensProtocol, publish_manifest=True)
googleLensAgent.run()
