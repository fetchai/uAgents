#import required libraries
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from models import Response, Response_list, Location
 
#restuarant agent's address
businessFinderAddress = "YOUR_BUSINESS_FINDER_AGENT_ADDRESS"

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
@user.on_interval(period=100.0, messages=Location)
async def interval(ctx: Context):
    #taking input for city and category from user
    city = str(input('What city you want to find business in?'))
    category = str(input('What category you want to find business for?'))  
    await ctx.send(businessFinderAddress, Location(city = city, category = category))

#Logging response from Business finder agent
@user.on_message(Response)
async def handle_query_response(ctx: Context, sender: str, msg: Response):
    ctx.logger.info(msg.response)
 
#running agent
#if __name__ == "__main__":
#    user.run()