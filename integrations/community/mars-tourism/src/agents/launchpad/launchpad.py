# Importing necessary modules and classes
from pydantic import Field
from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
from booking_protocol import booking_proto
from uagents import Agent, Protocol, Context, Model
import requests
import uuid

# Creating an agent named "Launchpad Agent" with a specific seed
launchpad_chooser_agent = Agent(name="Launchpad Agent", seed="40902090")

# Function to retrieve launchpads data from SpaceX API
async def get_launchpads():
   url = "https://api.spacexdata.com/v3/landpads"
   response = requests.get(url)
   launchpads = response.json()
   return launchpads

# Function to choose a launchpad based on its index
async def choose_launchpad(index):
    url = f"https://api.spacexdata.com/v3/landpads/{index}"
    response = requests.get(url)
    launchpad = response.json()
    return launchpad['full_name'] + " selected!" 

# Creating a protocol for launchpad choosing
launchpad_chooser_protocol = Protocol("LaunchpadChooser")

# Defining a Pydantic model for launchpad queries
class Launchpad(Model):
    query: str = Field(message="random string")

# Message handler for incoming launchpad queries
@launchpad_chooser_protocol.on_message(model=Launchpad, replies={UAgentResponse})
async def on_message(ctx: Context, sender: str, msg: Launchpad):
    # Retrieving launchpads data
    data = get_launchpads()
    options = []
    ctx_storage = {}
    # Generating a unique request ID
    request_id = str(uuid.uuid4())
    
    # Iterating through retrieved launchpads data to create options
    for idx, launchpad in enumerate(data):
        option = f"""● {idx+1}. {launchpad['full_name']} \n   Location: {launchpad['location']['name']},{launchpad['location']['region']}"""
        options.append(KeyValue(key=idx, value=option))
        ctx_storage[idx] = option
    # Storing options in context storage with the request ID
    ctx.storage.set(request_id, ctx_storage)

    # Sending options to the sender
    if options:
        await ctx.send(
            sender,
            UAgentResponse(
                options=options,
                type=UAgentResponseType.SELECT_FROM_OPTIONS,
                request_id=request_id
            ),
        )
    else:
        # Sending a message if no launchpads are found
        await ctx.send(
            sender,
            UAgentResponse(
                message="No launchpads found",
                type=UAgentResponseType.FINAL,
                request_id=request_id
            ),
        )

# Including the launchpad choosing protocol in the agent
launchpad_chooser_agent.include(launchpad_chooser_protocol)
# Including the booking protocol in the agent
launchpad_chooser_agent.include(booking_proto())
# Running the agent
launchpad_chooser_agent.run()
