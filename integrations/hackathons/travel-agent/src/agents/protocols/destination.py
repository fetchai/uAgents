from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
from typing import List
from uagents import Model, Protocol
from tomba.client import Client
from tomba.services.domain import Domain
import json 
json_file_path = "./info.json"
DESTINATIONS={}
with open(json_file_path, 'r') as json_file:
    data = json.load(json_file)
    
DESTINATIONS=data

class DestinationQuery(Model):
    budget: int
    activities: List[str]
    interests: List[str]

class DestinationResponse(Model):
    destinations: List[str]

query_proto= Protocol()
@query_proto.on_message(model= DestinationQuery, replies=DestinationResponse)
async def handle_destination_query(ctx: Context, sender: str, msg: DestinationQuery):
    recommended_destinations = []

    for destination, details in DESTINATIONS.items():
        if details["budget"] <= msg.budget and all(activity in details["activities"] for activity in msg.activities) and all(interest in details["interests"] for interest in msg.interests):
            recommended_destinations.append(destination)

    await ctx.send(sender, DestinationResponse(destinations=recommended_destinations))




