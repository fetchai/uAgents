# Here we demonstrate how we can create a simple dice roll agent that is compatible with DeltaV.
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType


class GoogleTool(Model):
    tool: str = Field(description="Which google tool you want to use? ")
    message : str

google_tool_protocol = Protocol("GoogleToolProtocol")


@google_tool_protocol.on_message(model=GoogleTool, replies={UAgentResponse})
async def google_tool(ctx: Context, sender: str, msg: GoogleTool):
    ctx.logger.info(f'User has selected google tool {msg.tool}')
    await ctx.send(sender, UAgentResponse(message = msg.message, type = UAgentResponseType.FINAL))
agent.include(google_tool_protocol, publish_manifest=True)
    