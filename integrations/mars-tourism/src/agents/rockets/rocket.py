# Import necessary modules and classes from external libraries
from pydantic import Field
from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
from booking_protocol import booking_proto
from uagents import Agent, Protocol, Context, Model
import requests
import uuid

# Create an agent instance for the rocket chooser functionality
rocket_chooser_agent = Agent(name="Rocket Agent", seed="60902090")

# Define an asynchronous function to retrieve rockets based on weight
async def get_rockets(weight):
   url = "https://api.spacexdata.com/v3/rockets"
   response = requests.get(url)
   rockets = response.json()
   return ([rocket for rocket in rockets if rocket['mass']['kg'] > int(weight)])

# Define a protocol for rocket choosing
rocket_chooser_protocol = Protocol("RocketChooser")

# Define a data model for rockets
class Rocket(Model):
    weight: str = Field(message="total weight of the person")
    
# Define behavior when receiving a rocket selection message
@rocket_chooser_protocol.on_message(model=Rocket, replies={UAgentResponse})
async def on_message(ctx: Context, sender: str, msg: Rocket):
    # Get the available rockets based on weight
    data = get_rockets(msg.weight)
    options=[]
    ctx_storage = {}
    request_id = str(uuid.uuid4())
    # Prepare options for user selection
    for idx, rocket in enumerate(data):
        option = f"""● {idx+1}. {rocket['rocket_name']}"""
        options.append(KeyValue(key=idx, value=option))
        ctx_storage[idx] = option
    # Store context information
    ctx_storage["weight"]=msg.weight
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
        # Send a message if no rockets are found
        await ctx.send(
            sender,
            UAgentResponse(
                message="No rockets found",
                type=UAgentResponseType.FINAL,
                request_id=request_id
            ),
        )

# Include the rocket chooser protocol and the booking protocol in the agent and run the agent
rocket_chooser_agent.include(rocket_chooser_protocol)
rocket_chooser_agent.include(booking_proto())
rocket_chooser_agent.run()
