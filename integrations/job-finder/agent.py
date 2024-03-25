import os
import sys
import langchain_openai
from pydantic import Field
import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol, Model
from uagents.setup import fund_agent_if_low
from langchain_community.utilities.google_jobs import GoogleJobsAPIWrapper
os.environ["SERPAPI_API_KEY"] = "xxxx" # use serp API
AGENT_MAILBOX_KEY = "xxxxx" # use actual mailbox key
# Extend your protocol with Wikipedia data fetching
class JobRequest(Model):
    job_description: str = Field(description="Give details of job you are looking for")
# Now your agent is ready to join the agentverse!
agent = Agent(
    name="jobs2",
    port=8000,
    seed="sangam_secretseed_jobs",
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
    endpoint=["http://127.0.0.1:8000/submit"],
)
print(f"Your agent's address is: {agent.address}")
job_protocol = Protocol("Job Finder Protocol")
@job_protocol.on_message(model=JobRequest, replies={UAgentResponse})
async def load_job(ctx: Context, sender: str, msg: JobRequest):
    wrapper = GoogleJobsAPIWrapper()
    result = wrapper.run(msg.job_description)
    await ctx.send(
        sender, UAgentResponse(message=result, type=UAgentResponseType.FINAL)
    )
agent.include(job_protocol, publish_manifest=True)
agent.run()