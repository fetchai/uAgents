# Here we demonstrate how we can create a DeltaV compatible agent responsible for getting Car Parking from Geoapify
# API. After running this agent, it can be registered to DeltaV on Agentverse's Services tab. For registration,
# you will have to use the agent's address.
#
# third party modules used in this example
import uuid

import requests
from ai_engine import UAgentResponse, UAgentResponseType, KeyValue
from pydantic import Field


class GeoParkingRequest(Model):
    latitude: float = Field(
        description="Describes the latitude where the user wants a Car parking. this shouldn't be the user location, "
        "but location of the place user specified"
    )
    longitude: float = Field(
        description="Describes the longitude where the user wants a Car parking. this shouldn't be the user location, "
        "but the location of the place the user specified."
    )
    radius: int = Field(
        description="Distance in miles, the maximum distance b/w car parking and the location provided by user"
    )
    max_result: int = Field(description="Number of Parking Names, that user wants.")


URL = "https://api.geoapify.com/v2/places?"

API_KEY = "YOUR_API_KEY"

if API_KEY == "YOUR_API_KEY":
    raise Exception(
        "You need to provide an API key for Google Maps to use this example"
    )

MAX_RESULTS = 10

parking_protocol_geoapi = Protocol("Geoapi CarParking")


def reform_data(api_response):
    """
    Reforms the Api Response into Options for Sending to Delta V.
    Args:
        api_response (Dict): Api Response From Geoapify API
    Returns:
        list or None: A list of Parking Space data if API is successful.
    """
    refactored_data = []
    parking_name = "Unknown"
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
                str(place["properties"]["datasource"]["raw"]["capacity"]) + " spaces"
            )
        elif "parking" in place["properties"]["datasource"]["raw"]:
            parking_capacity = (
                place["properties"]["datasource"]["raw"]["parking"] + " parking"
            )
        elif (
            "access" in place["properties"]["datasource"]["raw"]
            and place["properties"]["datasource"]["raw"]["access"] != "yes"
        ):
            continue
        refactored_data.append(
            f"""● This is Car Parking: {parking_name} has {parking_capacity} at {parking_address}"""
        )
    return refactored_data


def get_data(latitude, longitude, miles_radius) -> list or None:
    """
    Retrieves data from the Geoapify API for Car Parking.
    Args:
        latitude (float): The latitude coordinate.
        longitude (float): The longitude coordinate.
        miles_radius (float): The radius in miles for searching EV chargers.
    Returns:
        list or None: A list of Car Parking data if successful, or None if the request fails.
    """
    try:
        response = requests.get(
            url=f"{URL}categories=parking&filter=circle:{longitude},{latitude},{miles_radius}&bias=proximity:{longitude},{latitude}&limit={MAX_RESULTS}&apiKey={API_KEY}",
            timeout=60,
        )
        if response.status_code == 200:
            data = response.json()
            return reform_data(data)
        else:
            return None
    except requests.Timeout as e:
        print(
            "Request timed out. Check your internet connection or try again later.",
            str(e),
        )
    except requests.RequestException as e:
        print("An error occurred during the request:", str(e))
    except Exception as e:
        print("An unexpected error occurred:", str(e))


@parking_protocol_geoapi.on_message(model=GeoParkingRequest, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: GeoParkingRequest):
    ctx.logger.info(f"Received message from {sender}")
    try:
        radius_mtr = msg.radius * 1609
        response = get_data(msg.latitude, msg.longitude, radius_mtr)
        request_id = str(uuid.uuid4())
        options = []
        ctx_storage = {}
        for idx, parking in enumerate(response):
            option = parking
            options.append(KeyValue(key=idx, value=option))
            ctx_storage[idx] = option
        ctx.storage.set(request_id, ctx_storage)
        if options:
            await ctx.send(
                sender,
                UAgentResponse(
                    options=options,
                    type=UAgentResponseType.SELECT_FROM_OPTIONS,
                    request_id=request_id,
                ),
            )
        else:
            await ctx.send(
                sender,
                UAgentResponse(
                    message="No options are available for this context",
                    type=UAgentResponseType.FINAL,
                    request_id=request_id,
                ),
            )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR)
        )


agent.include(parking_protocol_geoapi)
