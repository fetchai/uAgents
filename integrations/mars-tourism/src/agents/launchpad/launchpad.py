# Import necessary modules and classes from external libraries
from pydantic import Field
from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
from booking_protocol import booking_proto
from uagents import Agent, Protocol, Context, Model
import requests
import uuid

# Create an agent instance for the launchpad chooser functionality
launchpad_chooser_agent = Agent(name="Launchpad Agent", seed="40902090")

# Define an asynchronous function to retrieve launchpads
async def get_launchpads():
   url = "https://api.spacexdata.com/v3/landpads"
   response = requests.get(url)
   launchpads = response.json()
   return launchpads

# Define an asynchronous function to choose a launchpad by index
async def choose_launchpad(index):
    url = f"https://api.spacexdata.com/v3/landpads/{index}"
    response = requests.get(url)
    launchpad = response.json()
    return launchpad['full_name'] + "selected!" 

# Define a protocol for launchpad choosing
launchpad_chooser_protocol = Protocol("LaunchpadChooser")

# Define a data model for launchpads
class Launchpad(Model):
    query: str = Field(message="random string")

# Define behavior when receiving a launchpad selection message
@launchpad_chooser_protocol.on_message(model=Launchpad, replies={UAgentResponse})
async def on_message(ctx: Context, sender: str, msg: Launchpad):
    # Get the available launchpads
    data = await get_launchpads()
    options=[]
    ctx_storage = {}
    request_id = str(uuid.uuid4())
    # Prepare options for user selection
    for idx, launchpad in enumerate(data):
        option = f"""● {idx+1}. {launchpad['full_name']} \n   Location: {launchpad['location']['name']},{launchpad['location']['region']}"""
        options.append(KeyValue(key=idx, value=option))
        ctx_storage[idx] = option
    # Store context information
    ctx.storage.set(request_id, ctx_storage)
    if options:
        # Send options for user selection
        await ctx.send(
            sender,
            UAgentResponse(
                options=options,
                type=UAgentResponseType.SELECT_FROM_OPTIONS,
                request_id=request_id
            ),
        )
    else:
        # Send a message if no launchpads are found
        await ctx.send(
            sender,
            UAgentResponse(
                message="No launchpads found",
                type=UAgentResponseType.FINAL,
                request_id=request_id
            ),
        )

# Include the launchpad chooser protocol and the booking protocol in the agent and run the agent
launchpad_chooser_agent.include(launchpad_chooser_protocol)
launchpad_chooser_agent.include(booking_proto())
launchpad_chooser_agent.run()
