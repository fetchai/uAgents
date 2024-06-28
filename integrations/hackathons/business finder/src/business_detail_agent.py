# importing required libraires
import requests
from uagents import Agent, Model, Context, Protocol
from uagents.setup import fund_agent_if_low
from models import Response, Response_list, Location

# Defining business details agent
business_agent = Agent(
    name = 'business_details_agent',
    port = 1123,
    seed = 'Business details agent secret seed phrase',
    endpoint = 'http://localhost:1123/submit'
)

# Funding business details agent
fund_agent_if_low(business_agent.wallet.address())

# Defining business details protocol
business_protocol = Protocol("Bussiness Details Protocol")

# Defining function to get details of opted business
async def business_list(name, city, category):
    # Calling API to get city's location coordinates
    url = "https://geocoding-by-api-ninjas.p.rapidapi.com/v1/geocoding"
    querystring = {"city":city}
    headers = {
	    "X-RapidAPI-Key": "GEO_CODING_API_KEY",
	    "X-RapidAPI-Host": "geocoding-by-api-ninjas.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    print(response)
    data = response.json()[0]
    longitude = str(data['longitude'])
    latitude = str(data['latitude'])
    # Calling API to get details for selected business
    url = "https://local-business-data.p.rapidapi.com/search-nearby"
    querystring = {"query":category,"lat":latitude,"lng":longitude,"limit":"10","language":"en"}
    headers = {
	    "X-RapidAPI-Key": "BUSINESS_API_KEY",
	    "X-RapidAPI-Host": "local-business-data.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    business = []
    data = response.json()['data']
    for i in range(10):
        if name.lower() == data[i]['name'].lower():
            link = data[i]['place_link']
            details = {'name': data[i]['name'],
            'phone_number': data[i]['phone_number'],
            'full_address': data[i]['full_address'],
            'rating': data[i]['rating'],
            'Google map link' : f"<a href='{link}'>Click Here</a>"
            }
            return details
            break
        else:
            continue
    
# Logging agent's address on startup
@business_agent.on_event('startup')
async def agent_address(ctx: Context):
    ctx.logger.info(business_agent.address)

# Handling business details request from business finder agent
@business_agent.on_message(model=Response_list, replies = Response)
async def bussiness_finder(ctx: Context, sender: str, msg: Response_list):
    # Logging list of businesses
    ctx.logger.info(msg.name_list)
    # Taking input from user to choose business name
    number = int(input('Please select item from list'))
    # Fetching business details from API
    business = await business_list(msg.name_list[number-1], msg.city, msg.category)
    business = str(business)
    # Logging busineess details
    ctx.logger.info(business)
    # Sending response to business finder agent    
    await ctx.send(sender, Response(response = business)) 

