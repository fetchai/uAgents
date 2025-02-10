import os

from uagents import Agent, Context

AGENT_NAME = os.environ.get("UAGENT_NAME", "agent")
AGENT_SEED = os.environ.get("UAGENT_SEED")
AGENT_TYPE = os.environ.get("UAGENT_TYPE", "custom")
AGENT_NETWORK = os.environ.get("UAGENT_NETWORK", "testnet")
AGENT_ENDPOINT = os.environ.get("UAGENT_ENDPOINT", "http://127.0.0.1:8000/submit")


agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    mailbox=AGENT_TYPE == "mailbox",
    proxy=AGENT_TYPE == "proxy",
    endpoint=AGENT_ENDPOINT,
    network=AGENT_NETWORK,
    publish_agent_details=True,
)


@agent.on_event("startup")
async def handle_startup(ctx: Context):
    ctx.logger.info("Agent has started")


@agent.on_interval(period=5)
async def handle_periodic(ctx: Context):
    ctx.logger.info("Agent is still alive")


if __name__ == "__main__":
    agent.run()
