# Importing required libraires
import requests
from ai_engine import UAgentResponse, UAgentResponseType
from uagents import Agent, Model, Context, Protocol
from uagents.setup import fund_agent_if_low
from models import Response, Response_list, Location

# Defining business protocol
business_protocol = Protocol("Bussiness Finder Protocol")

# Defining business finder angent 
business_finder = Agent(
    name = 'business_finder_agent',
    port = 1124,
    seed = 'Business finder agent secret seed phrase',
    endpoint = 'http://localhost:1124/submit'
)
# Funding business finder agent
fund_agent_if_low(business_finder.wallet.address())

# Defining function to get list of top 10 businesses in given location and category
async def business_list(city, category):
    # Calling API to get city's location coordinates
    url = "https://geocoding-by-api-ninjas.p.rapidapi.com/v1/geocoding"
    querystring = {"city":city}
    headers = {
	    "X-RapidAPI-Key": "GEO_CODING_API_KEY",
	    "X-RapidAPI-Host": "geocoding-by-api-ninjas.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()[0]
    longitude = str(data['longitude'])
    latitude = str(data['latitude'])
    # Calling API to get relevant businesses list coordinates
    url = "https://local-business-data.p.rapidapi.com/search-nearby"
    querystring = {"query":category,"lat":latitude,"lng":longitude,"limit":"10","language":"en"}
    headers = {
	    "X-RapidAPI-Key": "BUSINESS_API_KEY",
	    "X-RapidAPI-Host": "local-business-data.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    # defining empty business list
    business = []
    data = response.json()['data']
    #populating businesses in the business list.
    for i in range(10):
        details = data[i]['name']
        business.append(details)
    # Returning list of buiness's name.
    return business

# Logging business finders address on startup
@business_finder.on_event('startup')
async def agent_address(ctx: Context):
    ctx.logger.info(business_finder.address)

# Handling request for finding busines
@business_finder.on_message(model=Location, replies = Response_list)
async def bussiness_finder(ctx: Context, sender: str, msg: Location):
    # Fetching list of business using city and category
    business = await business_list(msg.city, msg.category)
    # Logging list of business
    ctx.logger.info(business)
    # Sending list to business details agent to fetch details of speicific business    
    await ctx.send('YOUR_BUSINESS_DETAILS_AGENT_ADDRESS', Response_list(city = msg.city, category = msg.category, name_list = business))

# Message Handler to send response to user
@business_finder.on_message(model=Response)
async def bussiness_finder(ctx: Context, sender: str, msg: Response):
    # Logging response from business details agent
    ctx.logger.info(msg.response)    
    # Sending response to the user
    await ctx.send('YOUR_USER_AGENT_ADDRESS', Response(response = msg.response))
