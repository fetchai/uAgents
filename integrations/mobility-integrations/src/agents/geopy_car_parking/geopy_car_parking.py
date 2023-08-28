import os
import uuid

import requests
from messages import GeoParkingRequest, KeyValue, UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low

GEOAPI_PARKING_SEED = os.getenv(
    "GEOAPI_PARKING_SEED", "geoapi parking adaptor agent secret phrase"
)
agent = Agent(name="geoapi_parking_adaptor", seed=GEOAPI_PARKING_SEED)
geoapi_parking_protocol = Protocol("Geoapi CarParking")

fund_agent_if_low(agent.wallet.address())

GEOAPI_API_KEY = os.getenv("GEOAPI_API_KEY", "")

assert GEOAPI_API_KEY, "GEOAPI_API_KEY environment variable is missing from .env"

PARKING_API_URL = "https://api.geoapify.com/v2/places?"


def format_parking_data(api_response) -> list:
    """
    By taking the response from the API, this function formats the response
    to be appropriate for displaying back to the user.
    """
    parking_data = []
    parking_name = "Unknown Parking"
    parking_capacity = ""
    for place in api_response["features"]:
        if "name" in place["properties"]:
            parking_name = place["properties"]["name"]
            address = place["properties"]["formatted"].split(",")[1::]
            parking_address = "".join(list(address))
        elif "formatted" in place["properties"]:
            parking_address = place["properties"]["formatted"]
        else:
            continue
        if "capacity" in place["properties"]["datasource"]["raw"]:
            parking_capacity = (
                f'{place["properties"]["datasource"]["raw"]["capacity"]} spaces'
            )
        elif "parking" in place["properties"]["datasource"]["raw"]:
            parking_capacity = (
                f'{place["properties"]["datasource"]["raw"]["parking"]} parking'
            )
        elif (
            "access" in place["properties"]["datasource"]["raw"]
            and place["properties"]["datasource"]["raw"]["access"] != "yes"
        ):
            continue
        parking_data.append(
            f"""● Car Parking: {parking_name} has {parking_capacity} at {parking_address}"""
        )
    return parking_data


def get_parking_from_api(latitude, longitude, radius, max_r) -> list:
    """
    With all the user preferences, this function sends the request to the Geoapify Parking API,
    which returns the response.
    """
    try:
        response = requests.get(
            url=f"{PARKING_API_URL}categories=parking&filter=circle:{longitude},{latitude},{radius}&bias=proximity:{longitude},{latitude}&limit={max_r}&apiKey={GEOAPI_API_KEY}",
            timeout=60,
        )
        return response.json()
    except Exception as exc:
        print("Error: ", exc)
        return []


@geoapi_parking_protocol.on_message(model=GeoParkingRequest, replies=UAgentResponse)
async def geoapi_parking(ctx: Context, sender: str, msg: GeoParkingRequest):
    """
    The function takes the request to search for parking in any location based on user preferences
    and returns the formatted response to TAGI.
    """
    ctx.logger.info(f"Received message from {sender}")
    try:
        radius_in_meter = msg.radius * 1609
        response = get_parking_from_api(
            msg.latitude, msg.longitude, radius_in_meter, msg.max_result
        )  # Sending user preferences to find nearby parking spaces.
        response = format_parking_data(
            response
        )  # Sending the API response to be made appropriate to users.
        request_id = str(uuid.uuid4())
        if len(response) > 1:
            option = f"""Here is the list of some Parking spaces nearby:\n"""
            idx = ""
            options = [KeyValue(key=idx, value=option)]
            for parking in response:
                option = parking
                options.append(KeyValue(key=idx, value=option))
            await ctx.send(
                sender,
                UAgentResponse(
                    options=options,
                    type=UAgentResponseType.SELECT_FROM_OPTIONS,
                    request_id=request_id,
                ),
            )  # Sending the response bach to users.
        else:
            await ctx.send(
                sender,
                UAgentResponse(
                    message="No options available for this context",
                    type=UAgentResponseType.FINAL,
                    request_id=request_id,
                ),
            )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR)
        )


agent.include(geoapi_parking_protocol)
