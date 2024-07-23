# import required libraries
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from message.model import Response, Code
import os
 
# restuarant agent's address
flight_agent = "agent1qf8n5m7ruhy34xfmsepuntznlffzejt4zey9ftfhxwgqst6se4w4g7tpsx4"

#defining user agent
user = Agent(
    name="user",
    port=8000,
    seed="user secret phrase",
    endpoint=["http://localhost:8000/submit"],
)
 
 #funding user agent
fund_agent_if_low(user.wallet.address())
 
#checking user agent's address
@user.on_event('startup')
async def agent_address(ctx: Context):
    ctx.logger.info(user.address)
 
# This on_interval agent function performs a request on a defined period of 100 seconds
@user.on_interval(period=30, messages=Code)
async def interval(ctx: Context):
    #taking input for city and category from user
    flight = str(input('Please enter flight number to get details.'))
    await ctx.send(flight_agent, Code(code = flight))

#Logging response from Business finder agent
@user.on_message(Response)
async def handle_query_response(ctx: Context, sender: str, msg: Response):
    ctx.logger.info(msg.response)
 