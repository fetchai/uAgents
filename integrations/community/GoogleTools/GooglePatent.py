import os
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
from serpapi import GoogleSearch

def get_concise_patent_info(query,api_key):
    params = {
        "engine": "google_patents",
        "q": query,
        "api_key": api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results.get("organic_results", [])

    res_str = ""
    for result in organic_results[:1]:  # Adjust the number of results here
        title = result.get('title', 'N/A')
        patent_id = result.get('patent_id', '').split('/')[-1]
        assignee = result.get('assignee', 'N/A')
        link = result.get('serpapi_link', '#')
        res_str += (
            f"Title: {title}\n"
            f"Patent ID: {patent_id}\n"
            f"Assignee: {assignee}\n"
            f"Details: <a href='{link}'>View Patent</a>\n\n"
        )

    return res_str if res_str else "No results found."


# Define the request model for your business analysis
class GoogleTrendRequest(Model):
    trend: str = Field(description="Ask query to be check trend for? ")

# Initialize your agent
SEED_PHRASE = "Google Trend Seed Phrase"
AGENT_MAILBOX_KEY = "<Your_mailbox_api_key>"
googleTrendAgent = Agent(
    name="Google Trend Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)
print(googleTrendAgent.address)
# Fund the agent if needed
fund_agent_if_low(googleTrendAgent.wallet.address())

# Define a protocol for handling business analysis requests
googleTrendProtocol = Protocol("Google Trends Protocol")

# Define the behavior when a message is received
@googleTrendProtocol.on_message(model=GoogleTrendRequest, replies={UAgentResponse})
async def handle_business_analysis_request(ctx: Context, sender: str, msg: GoogleTrendRequest):
    ctx.logger.info(f'User has requested details for {msg.trend}')
    api_key = os.getenv('google_patent_api_key')
    details = get_concise_patent_info(msg.trend, api_key)
    ctx.logger.info(details)
    await ctx.send(sender, UAgentResponse(message=details, type=UAgentResponseType.FINAL))

# Start the agent
googleTrendAgent.include(googleTrendProtocol, publish_manifest=True)
googleTrendAgent.run()
