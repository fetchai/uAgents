from uagents import Agent, Context
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

from protocols import picker_proto

# Copy the address printed when menu_host.py starts.
MENU_HOST_ADDRESS = "agent1q0jycdv6z8cppknsgl98ee669futsme2zmmpm5qajdy675x5gefu288zrd2"

agent = Agent(
    name="picker-staging",
    port=8001,
    mailbox=True,
    agentverse="https://staging.agentverse.ai",
)
agent.include(picker_proto)


@agent.on_event("startup")
async def request_menu(ctx: Context):
    if MENU_HOST_ADDRESS.startswith("paste"):
        ctx.logger.warning(
            "Set MENU_HOST_ADDRESS in picker.py to the menu-host agent address"
        )
        return
    ctx.logger.info("Requesting menu from %s", MENU_HOST_ADDRESS)
    await ctx.send(MENU_HOST_ADDRESS, ChatMessage([TextContent("menu")]))


if __name__ == "__main__":
    agent.run()
