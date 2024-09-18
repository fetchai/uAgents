# import required libraries
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from message.model import Response, Location

# restuarant agent's address
londonTransportAgent = (
    "YOUR_TRANSPORT_AGENT_ADDRESS"  # replace with your london transport agent
)

# defining user agent
user = Agent(
    name="user",
    port=8000,
    seed="user secret phrase",
    endpoint=["http://localhost:8000/submit"],
)

# funding user agent
fund_agent_if_low(user.wallet.address())


# checking user agent's address
@user.on_event("startup")
async def agent_address(ctx: Context):
    ctx.logger.info(user.address)


# This on_interval agent function performs a request on a defined period of 100 seconds
@user.on_interval(period=100.0, messages=Location)
async def interval(ctx: Context):
    # taking input for city and category from user
    from_loc = str(input("From where you want to travel using london transport?"))
    to_loc = str(input("To where you want to travel using london transport?"))
    await ctx.send(londonTransportAgent, Location(from_loc=from_loc, to_loc=to_loc))


# Logging response from Business finder agent
@user.on_message(Response)
async def handle_query_response(ctx: Context, sender: str, msg: Response):
    ctx.logger.info(msg.response)
