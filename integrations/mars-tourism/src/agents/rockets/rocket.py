# Importing necessary modules and classes
from pydantic import Field
from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
from booking_protocol import booking_proto  # Importing the previously defined booking protocol
from uagents import Agent, Protocol, Context, Model
import requests
import uuid

# Creating an agent named "Rocket Agent" with a specific seed
rocket_chooser_agent = Agent(name="Rocket Agent", seed="60902090")

# Function to retrieve rockets data from SpaceX API based on weight
async def get_rockets(weight):
   url = "https://api.spacexdata.com/v3/rockets"
   response = requests.get(url)
   rockets = response.json()
   # Filtering rockets based on weight criteria
   return [rocket for rocket in rockets if rocket['mass']['kg'] > int(weight)]

# Creating a protocol for rocket choosing
rocket_chooser_protocol = Protocol("RocketChooser")

# Defining a Pydantic model for rocket queries
class Rocket(Model):
    weight: str = Field(message="total weight of the person")

# Message handler for incoming rocket queries
@rocket_chooser_protocol.on_message(model=Rocket, replies={UAgentResponse})
async def on_message(ctx: Context, sender: str, msg: Rocket):
    # Retrieving rockets data based on weight
    data = get_rockets(msg.weight)
    options = []
    ctx_storage = {}
    # Generating a unique request ID
    request_id = str(uuid.uuid4())
    
    # Iterating through retrieved rockets data to create options
    for idx, rocket in enumerate(data):
        option = f"""● {idx+1}. {rocket['rocket_name']}"""
        options.append(KeyValue(key=idx, value=option))
        ctx_storage[idx] = option
    # Storing options and weight in context storage with the request ID
    ctx_storage["weight"] = msg.weight
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
        # Sending a message if no rockets are found
        await ctx.send(
            sender,
            UAgentResponse(
                message="No rockets found",
                type=UAgentResponseType.FINAL,
                request_id=request_id
            ),
        )

# Including the rocket choosing protocol in the agent
rocket_chooser_agent.include(rocket_chooser_protocol)
# Including the booking protocol in the agent
rocket_chooser_agent.include(booking_proto())
# Running the agent
rocket_chooser_agent.run()
