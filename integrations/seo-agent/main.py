import os

from pydantic import Field

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol, Model
from wrapper import startProcess

from ai_engine import UAgentResponse, UAgentResponseType

load_dotenv()

AGENT_SEED = os.environ["AGENT_SEED"]
if not AGENT_SEED:
    raise ValueError("AGENT_SEED not set in .env file")

MAILBOX_API_KEY = os.environ["MAILBOX_API_KEY"]

agent = Agent(
    name="seo-agent",
    seed=AGENT_SEED,
    mailbox=f"{MAILBOX_API_KEY}@https://agentverse.ai",
)

class SeoRequest(Model):
    url: str = Field(
        description="The url of the website the user wants to have analyzed for its SEO ranking and performance and to get recommendations how to improve it"
    )

@agent.on_message(SeoRequest, replies=UAgentResponse)
async def handle_agent_message(ctx: Context, sender: str, msg: SeoRequest):
    ctx.logger.info(
        f"Received message from DeltaV: {msg.url}"
    )
    result = startProcess(msg.url)
    ctx.logger.info(f"Sending result to DV: {result}")
    await ctx.send(
        sender,
        UAgentResponse(message=result, type=UAgentResponseType.FINAL))


seo_deltav_protocol = Protocol(name="seo-dv", version="0.1.0")

if __name__ == "__main__":
    agent.include(seo_deltav_protocol, publish_manifest=True)
    agent.run()