# Import necessary modules and classes from external libraries
from pydantic import Field
from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
import requests
from uagents import Agent, Protocol, Context, Model

# Create an agent instance for the space trip functionality
space_trip_agent = Agent(name="Space Trip Agent", seed="50902090")

# Define a custom protocol for the space trip functionality
space_trip_protocol = Protocol("SpaceTrip")

# Define a data model for the rocket
class Rocket(Model):
    weight: str = Field(message="total weight of the person")

# Define a data model for the space trip
class SpaceTrip(Model):
    launchpad: str = Field(message="Name of the launchpad retrieved from the subtask. DO NOT ASK THIS FROM THE USER")
    rocket: str = Field(message="Name of the rocket retrieved from the subtask. DO NOT ASK THIS FROM THE USER")
    start_date: str = Field(message="Date of the day you want to go for trip. Ask from the user using a calendar interface allowing users to enter future (format=YYYY-MM-DD)")

# Function to check sky conditions on a specific date using NASA API
def sky_condition(date):
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={date}&end_date={date}&api_key=po3nZGZhoOlU8J5rfeWMbOFglvhWtQsxaesWkioh"
    response = requests.get(url)
    if(response.json()['element_count'] < 10):
        return True
    else:
        return False

# Define behavior when receiving a space trip message
@space_trip_protocol.on_message(model=SpaceTrip, replies={UAgentResponse})
async def on_message(ctx: Context, sender: str, msg: SpaceTrip):
    if(sky_condition(msg.start_date)):
        # Send a response with the order summary if sky conditions are suitable
        await ctx.send(sender, UAgentResponse(message="Order Summary: \n"+"Launchpad: "+msg.launchpad+"\nRocket: "+msg.rocket, type=UAgentResponseType.FINAL))
    else:
        # Send a warning along with the order summary if sky conditions are not suitable
        await ctx.send(sender, UAgentResponse(message="Order Summary: \n"+"Launchpad: "+msg.launchpad+"\nRocket: "+msg.rocket+ "\nWarning: Too many interferences were found on the selected date. Do your thing at your own risk", type=UAgentResponseType.FINAL))

# Include the protocol in the agent and run the agent
space_trip_agent.include(space_trip_protocol)
space_trip_agent.run()
