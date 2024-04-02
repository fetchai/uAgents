import os
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
from serpapi import GoogleSearch

def get_concise_scholar_info(query, api_key):
    params = {
      "engine": "google_scholar",
      "q": query,
      "api_key": api_key  # Replace with your actual API key
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])

    res_str = ""
    for result in organic_results[:3]:  # Get first three results only
        title = result.get('title', 'N/A')
        link = result.get('link', 'N/A')
        snippet = result.get('snippet', 'N/A')
        publication_info = result.get('publication_info', {}).get('summary', 'N/A')
        res_str += (
            f"Title: {title}\n"
            f"Publication Info: {publication_info}\n"
            f"Summary: {snippet}\n"
            f"Link: <a href='{link}'>Read More</a>\n\n"
        )

    return res_str if res_str else "No results found."


# Define the request model for your business analysis
class GoogleScholarRequest(Model):
    query: str = Field(description="Enter the query for which you want to do scholar search")

# Initialize your agent
SEED_PHRASE = "Google Scholar Seed Phrase"
AGENT_MAILBOX_KEY = "ff20b0ce-7c24-4c93-bcc5-feb3ba70067c"
googleScholarAgent = Agent(
    name="Google Scholar Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)
print(googleScholarAgent.address)
# Fund the agent if needed
fund_agent_if_low(googleScholarAgent.wallet.address())

# Define a protocol for handling business analysis requests
googleScholarProtocol = Protocol("Google Scholar Protocol")

# Define the behavior when a message is received
@googleScholarProtocol.on_message(model=GoogleScholarRequest, replies={UAgentResponse})
async def handle_business_analysis_request(ctx: Context, sender: str, msg: GoogleScholarRequest):
    ctx.logger.info(f'User has requested details for {msg.query}')
    api_key = "02b5b4017b9b6ffa28303f94b2c2d6ac4e62a3e4f61f88e0242c533fe6142619"
    details = get_concise_scholar_info(msg.query,api_key)
    ctx.logger.info(str(details))
    await ctx.send(sender, UAgentResponse(message=str(details), type=UAgentResponseType.FINAL))

# Start the agent
googleScholarAgent.include(googleScholarProtocol, publish_manifest=True)
googleScholarAgent.run()