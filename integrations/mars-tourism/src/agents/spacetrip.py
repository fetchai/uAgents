# Importing necessary modules and classes
from pydantic import Field
from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
from uagents import Agent, Protocol, Context, Model
import requests
import uuid

# Creating an agent named "Space Trip Agent" with a specific seed
space_trip_agent = Agent(name="Space Trip Agent", seed="50902090")

# Defining a protocol for space trips
space_trip_protocol = Protocol("SpaceTrip")

# Defining Pydantic models for rocket and space trip details
class Rocket(Model):
    weight: str = Field(message="total weight of the person")

class SpaceTrip(Model):
    launchpad: str = Field(message="Name of the launchpad retrieved from the subtask. DO NOT ASK THIS FROM THE USER")
    rocket: str = Field(message="Name of the rocket retrieved from the subtask. DO NOT ASK THIS FROM THE USER")
    weight: str = Field(message="Weight of the person retrieved from the subtask. DO NOT ASK THIS FROM THE USER")
    start_date: str = Field(message="Date of the day you want to go for trip. Ask from the user using a calendar interface allowing users to enter future (format=YYYY-MM-DD)")

# Function to check sky condition on a given date
def sky_condition(date):
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={date}&end_date={date}&api_key=po3nZGZhoOlU8J5rfeWMbOFglvhWtQsxaesWkioh"
    response = requests.get(url)
    jsonRes = response.json()
    if(jsonRes['element_count'] < 10):
        return True
    else:
        return False

# Function to generate payment link
def get_payment_link(launchpad, rocket, weight):
    data = {
        "items": [
            {
                "name": rocket + " - " + launchpad,
                "images": ["https://ideogram.ai/api/images/direct/X4G1M6GTTm-AQ7KK7pSSqw.jpg"],
                "quantity": 1,
                "price": int(weight)*10000
            }
        ],
        "email": "martiantrip@martiantrip.com"
    }

    response = requests.post("https://pixathon2024.vercel.app/api/checkout", json=data)
    link = response.json()['session_url']
    return link

# Message handler for incoming space trip requests
@space_trip_protocol.on_message(model=SpaceTrip, replies={UAgentResponse})
async def on_message(ctx: Context, sender: str, msg: SpaceTrip):
    if(sky_condition(msg.start_date)):
        # If sky condition is favorable, generate payment link and send order summary
        link = await get_payment_link(msg.launchpad, msg.rocket, msg.weight)
        await ctx.send(sender, UAgentResponse(message="Order Summary: \n"+"Launchpad: "+msg.launchpad+"\nRocket: "+msg.rocket+"\nCost: Rs."+str(int(msg.weight)*10000)+'\nPayment link: <a href="'+link+ '">Pay here</a>', type=UAgentResponseType.FINAL))
    else:
        # If sky condition is not favorable, send warning message along with payment link
        link = await get_payment_link(msg.launchpad, msg.rocket, msg.weight)
        await ctx.send(sender, UAgentResponse(message="Order Summary: \n"+"Launchpad: "+msg.launchpad+"\nRocket: "+msg.rocket+"\nCost: Rs."+str(int(msg.weight)*10000)+'\nPayment link: <a href="'+link+'">Pay here</a>'+"\n\nWarning: Too many interferences(asteroids) were found on the selected date. Do your thing at your own risk", type=UAgentResponseType.FINAL))

# Including the space trip protocol in the agent and running it
space_trip_agent.include(space_trip_protocol)
space_trip_agent.run()
