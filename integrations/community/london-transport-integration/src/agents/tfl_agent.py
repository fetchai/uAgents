# importing required libraries
import requests
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from message.model import Response, Location


# defining london transport angent
london_transport = Agent(
    name="london_transport_agent",
    port=1123,
    seed="London Transport agent secret seed phrase",
    endpoint="http://localhost:1123/submit",
)

# funding london transport agent
fund_agent_if_low(london_transport.wallet.address())


# define function to get postcode from area name
async def get_area_pincode(area_name: str):
    api_key = "YOUR_RAPID_API_KEY"  # Replace with your actual RapidAPI key
    base_url = "https://uk-postcode.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Host": "uk-postcode.p.rapidapi.com",
        "X-RapidAPI-Key": api_key,
    }
    querystring = {"q": area_name}
    try:
        response = requests.get(base_url, headers=headers, params=querystring)
        response.raise_for_status()  # Raises an HTTPError if the response was an error
        data = response.json()
        pinCode = data["results"][0]["postCode"]
        return pinCode
    except (requests.RequestException, IndexError) as e:
        print(f"Error fetching pin code for {area_name}: {e}")
        return None


# define function to get possible routes from location1 to location2
async def get_journey_data(loc1_pin, loc2_pin):
    try:
        tfl_url = (
            f"https://api.tfl.gov.uk/Journey/JourneyResults/{loc1_pin}/to/{loc2_pin}"
        )
        reply = requests.get(tfl_url)
        reply.raise_for_status()  # Check for HTTP errors
        data = reply.json()
        return data
    except requests.RequestException as e:
        print(f"Error fetching journey data: {e}")
        return None


# checking user agent's address
@london_transport.on_event("startup")
async def agent_address(ctx: Context):
    ctx.logger.info(london_transport.address)


# Define Message handler to handle user request
@london_transport.on_message(model=Location, replies=Response)
async def handle_request(ctx: Context, sender: str, msg: Location):
    # Get pin codes for the locations
    loc1_pin = await get_area_pincode(msg.from_loc)
    loc2_pin = await get_area_pincode(msg.to_loc)

    response = ""  # Initialize an empty string to hold the response

    if loc1_pin and loc2_pin:
        # Make the initial TfL API request
        journey_data = await get_journey_data(loc1_pin, loc2_pin)
        for journey in journey_data["journeys"]:
            response += f"Start Time: {journey['startDateTime']}\n"
            response += f"Duration: {journey['duration']} minutes\n"
            response += f"Arrival Time: {journey['arrivalDateTime']}\n"

            # Loop through each leg of the journey
            for leg in journey["legs"]:
                mode = leg["mode"]["name"]
                departure_time = leg["departureTime"]
                arrival_time = leg["arrivalTime"]
                distance = leg.get(
                    "distance", "N/A"
                )  # Some legs might not have distance information

                # Append leg details to the response string
                response += f"\nLeg Mode: {mode}\n"
                response += f"Departure Time: {departure_time}\n"
                response += f"Arrival Time: {arrival_time}\n"
                response += f"Distance: {distance} meters\n"

                # Instruction details if available
                if "instruction" in leg:
                    instruction_summary = leg["instruction"]["summary"]
                    response += f"Instructions: {instruction_summary}\n"

            response += "\n--------------------------------\n"
    # Sending back response to user agent
    await ctx.send(sender, Response(response=response))
