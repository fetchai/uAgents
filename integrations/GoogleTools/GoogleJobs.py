import os
from serpapi import GoogleSearch
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

def get_job_summary(query, api_key):
    # Parameters for the API request
    params = {
      "engine": "google_jobs",
      "q": query,
      "hl": "en",
      "api_key": api_key
    }

    # Perform the search
    search = GoogleSearch(params)
    results = search.get_dict()
    jobs_results = results.get("jobs_results", [])
    
    # Initialize the result string
    res_str = ""
    # Get summary for the first job result
    if jobs_results:
        job = jobs_results[0]  # Get the first job
        res_str += (
            "\n_______________________________________________"
            + f"\nJob Title: {job.get('title', 'N/A')}\n"
            + f"Company Name: {job.get('company_name', 'N/A')}\n"
            + f"Location: {job.get('location', 'N/A')}\n"
            + f"Posted: {job['detected_extensions'].get('posted_at', 'N/A')}\n"
            + f"Type: {job['detected_extensions'].get('schedule_type', 'N/A')}\n"
            + f"Description: {job.get('description', 'N/A')[:500]}"
            + "\n_______________________________________________\n"
        )
    else:
        res_str = "No job results found."

    return res_str


# Define the request model for your business analysis
class GoogleJobsRequest(Model):
    job_query: str = Field(description="Please describe what type of Job are you looking for? ")

# Initialize your agent
SEED_PHRASE = "Google Jobs Seed Phrase"
AGENT_MAILBOX_KEY = "41a4ad0f-0a28-4021-9740-d716488f28e8"
googleJobsAgent = Agent(
    name="Google Jobs Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)
print(googleJobsAgent.address)
# Fund the agent if needed
fund_agent_if_low(googleJobsAgent.wallet.address())

# Define a protocol for handling business analysis requests
googleJobsProtocol = Protocol("Google Jobs Protocol")

# Define the behavior when a message is received
@googleJobsProtocol.on_message(model=GoogleJobsRequest, replies={UAgentResponse})
async def handle_business_analysis_request(ctx: Context, sender: str, msg: GoogleJobsRequest):
    ctx.logger.info(f'User has requested details for {msg.job_query}')
    api_key = "02b5b4017b9b6ffa28303f94b2c2d6ac4e62a3e4f61f88e0242c533fe6142619"
    response = get_job_summary(msg.job_query,api_key)
    ctx.logger.info(str(response))
    await ctx.send(sender, UAgentResponse(message=str(response), type=UAgentResponseType.FINAL))

# Start the agent
googleJobsAgent.include(googleJobsProtocol, publish_manifest=True)
googleJobsAgent.run()