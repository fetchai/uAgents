# Here we demonstrate how we can create a DeltaV compatible agent responsible for getting Geo Coordinates from the
# Google Map API. After running this agent, it can be registered to DeltaV on Agentverse's Services tab. For
# registration, you will have to use the agent's address.
#
# third party modules used in this example
import uuid
from typing import Tuple
import requests
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field


class GeoCode(Model):
    address: str = Field(description="Address of a location to find lat and long of.")


URL = "https://maps.googleapis.com/maps/api/geocode/json"

API_KEY = "YOUR_API_KEY"

if API_KEY == "YOUR_API_KEY":
    raise Exception("You need to provide an API key for Google Maps API to use this example")

geocode_protocol = Protocol("GeoCode")


def get_data(address: str) -> Tuple or None:
    """
    Returns the latitude and longitude of a location using the Google Maps Geocoding API.
    Args:
        address (str): The address of the location.
    Returns:
        tuple: A tuple containing the latitude and longitude of the location.
    """
    query_params = {"key": f"{API_KEY}", "address": f"{address}"}
    response = requests.get(URL, params=query_params)
    data = response.json()
    if data['status'] == 'OK':
        latitude = data['results'][0]['geometry']['location']['lat']
        longitude = data['results'][0]['geometry']['location']['lng']
        return latitude, longitude
    else:
        return None


@geocode_protocol.on_message(model=GeoCode, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: GeoCode):
    ctx.logger.info(f"Received message from {sender}.")
    try:
        data = get_data(msg.address)
        request_id = str(uuid.uuid4())
        latitude, longitude = data
        option = f"""Location for {msg.address} is: \nlatitude={latitude}, longitude={longitude}"""
        ctx.storage.set(request_id, option)
        if latitude and longitude:
            await ctx.send(
                sender,
                UAgentResponse(
                    message=option,
                    type=UAgentResponseType.FINAL,
                    request_id=request_id
                ),
            )
        else:
            await ctx.send(
                sender,
                UAgentResponse(
                    message="No geo coordinates are available for this context",
                    type=UAgentResponseType.FINAL,
                    request_id=request_id
                ),
            )

    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender,
            UAgentResponse(
                message=str(exc),
                type=UAgentResponseType.ERROR
            )
        )


agent.include(geocode_protocol)
