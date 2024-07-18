import requests
from uagents import Agent, Model, Context, Protocol
from uagents.setup import fund_agent_if_low
from message.model import Response, Code
import os
from datetime import datetime

# Importing required libraries
import requests
from datetime import datetime

# Defining London transport agent
flight_data = Agent(
    name='flight_data_agent',
    port=1123,
    seed='Flight data agent secret seed phrase',
    endpoint='http://localhost:1123/submit'
)

# Funding London transport agent
fund_agent_if_low(flight_data.wallet.address())

@flight_data.on_event('startup')
async def address(ctx: Context):
    # Logging the flight data agent address on startup
    ctx.logger.info(flight_data.address)

async def unix_to_readable(timestamp):
    """Convert Unix timestamp to a readable date-time string."""
    if timestamp:
        # Converting Unix timestamp to human-readable format
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return "Not available"

async def get_flight_details_by_number(flight_number):
    """Fetch and return detailed flight information based on flight number."""
    # Initial API call to search for the flight
    search_url = "https://flight-radar1.p.rapidapi.com/flights/search"
    search_querystring = {"query": flight_number, "limit": "1"}  # Assuming we're interested in the most relevant result
    headers = {
        "X-RapidAPI-Key": "Your-RapidAPI-Key",
        "X-RapidAPI-Host": "flight-radar1.p.rapidapi.com",
    }
    
    # Making a request to the search API
    search_response = requests.get(search_url, headers=headers, params=search_querystring)
    if search_response.status_code == 200 and search_response.json():
        # Extracting flight ID from search response
        flight_id = search_response.json()['results'][0]['id']
        
        # API call to get detailed flight information using the flight ID
        detail_url = "https://flight-radar1.p.rapidapi.com/flights/detail"
        detail_querystring = {"flight": flight_id}
        
        # Making a request to the detail API
        detail_response = requests.get(detail_url, headers=headers, params=detail_querystring)
        if detail_response.status_code == 200:
            flight_details = detail_response.json()
            if 'airport' in flight_details and 'origin' in flight_details['airport'] and 'destination' in flight_details['airport']:
                # Extracting relevant flight details
                origin_airport = flight_details['airport']['origin']['name']
                destination_airport = flight_details['airport']['destination']['name']
                scheduled_departure = await unix_to_readable(flight_details['time']['scheduled']['departure'])
                scheduled_arrival = await unix_to_readable(flight_details['time']['scheduled']['arrival'])
                estimated_arrival = await unix_to_readable(flight_details['time']['estimated']['arrival']) if flight_details['time'].get('estimated', {}).get('arrival') else "Not available"
                
                # Compiling flight details into a string
                details = f"Flight Number: {flight_number}\nFrom: {origin_airport}\nTo: {destination_airport}\nScheduled Departure: {scheduled_departure}\nScheduled Arrival: {scheduled_arrival}\nEstimated Arrival: {estimated_arrival}\n"
                
                last_point = flight_details['trail'][-1]

                # Preparing to make a request for the current location based on the last known coordinates
                geo_url = "https://geocodeapi.p.rapidapi.com/GetNearestCities"
                headers1 = {
                    "X-RapidAPI-Key": "Your-RapidAPI-Key",
                    "X-RapidAPI-Host": "geocodeapi.p.rapidapi.com"
                }
                geo_querystring = {"latitude": str(last_point['lat']), "longitude": str(last_point['lng']), "range": "0"}
                    
                # Making a request to the google-maps-geocode API
                geo_response = requests.get(geo_url, headers=headers1, params=geo_querystring)
            else:
                return f"Failed to retrieve detailed flight information for flight ID {flight_id}."

            if geo_response.status_code == 200 and geo_response.json():
                # Extracting the current city from the google-maps-geocode response
                current_city = geo_response.json()[0]['City']
                details += f"Present Location: {current_city}"
            else:
                details += "Present Location: Data not available"
            return details
        else:
            return f"Failed to retrieve detailed flight information for flight ID {flight_id}."
    else:
        return "No results found for the provided flight number."

@flight_data.on_message(model = Code, replies= Response)
async def flight_details(ctx: Context, sender: str, msg: Code):
    # Processing flight details request
    flight_number = msg.code
    flight_details = await get_flight_details_by_number(flight_number)
    # Sending flight details response
    await ctx.send(sender, Response(response = flight_details))
