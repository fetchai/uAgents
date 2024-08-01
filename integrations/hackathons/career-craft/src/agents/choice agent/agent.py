from uagents import Context, Model, Protocol
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field
import json
import requests

class Request(Model):
    choice: str
    response: str

simplesmain = Protocol(name = "Choice Agent")

@simplesmain.on_message(model=Request, replies = UAgentResponse)
async def on_news_request(ctx: Context, sender: str, msg: Request):
    #Printing the news response on logger
    ctx.logger.info(f"Received choice request from {sender} with title: {msg.choice}")
    #Creating hyperlink and sending final response to the DeltaV GUI
    await ctx.send(sender, UAgentResponse(message = msg.response, type = UAgentResponseType.FINAL))
 
 
# Include the Generate Request protocol in your agent
agent.include(simplesmain)