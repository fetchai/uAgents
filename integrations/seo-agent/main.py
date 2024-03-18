import os
import asyncio

from asyncio.tasks import concurrent
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

seo_deltav_protocol = Protocol(name="seo-dv", version="0.2.0")
class SeoRequest(Model):
    url: str = Field(
        description="The url of the website the user wants to have analyzed for its SEO ranking and performance and to get recommendations how to improve it. It needs to start with 'https://'"
    )

async def asyncCall(url: str):
    # ugly hack
    with concurrent.futures.ProcessPoolExecutor() as exec:
        return await asyncio.get_event_loop().run_in_executor(exec, startProcess, url)

@seo_deltav_protocol.on_message(SeoRequest, replies={UAgentResponse})
async def handle_agent_message(ctx: Context, sender: str, msg: SeoRequest):
    ctx.logger.info(
        f"Received message from DeltaV: {msg.url}"
    )
    try:
        result = await asyncCall(msg.url)
        ctx.logger.info(f"Sending result to DV: {result}")
        await ctx.send(
            sender,
            UAgentResponse(message=result, type=UAgentResponseType.FINAL))
    except Exception as e:
        print(e.__traceback__)
        await ctx.send(sender, UAgentResponse(message="Unexpected Error", type=UAgentResponseType.ERROR))


agent.include(seo_deltav_protocol, publish_manifest=True)

if __name__ == "__main__":
    # print(seo_deltav_protocol.manifest())
    # print(agent.address)
    agent.run()