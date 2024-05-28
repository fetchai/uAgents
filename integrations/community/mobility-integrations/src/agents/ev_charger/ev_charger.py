# Here we demonstrate how we can create a DeltaV compatible agent responsible for getting EV Chargers from the open
# chargemap API. After running this agent, it can be registered to DeltaV on Agentverse's Services tab. For
# registration, you will have to use the agent's address.
#
# third party modules used in this example
import uuid
import requests
from ai_engine import KeyValue, UAgentResponse, UAgentResponseType
from pydantic import Field

# modules from booking_protocol.py
from booking_protocol import booking_proto


class EvRequest(Model):
    latitude: float = Field(
        description="Describes the latitude where the user wants an EV charger. This might not be the user current "
                    "location, if user specified a specific location on the objective.")
    longitude: float = Field(
        description="Describes the longitude where the user wants an EV charger. This might not be the user current "
                    "location, if user specified a specific location on the objective.")
    miles_radius: float = Field(
        description="Distance in miles, the maximum distance b/w ev charger and the location provided by user")


# To use this example, you will need to provide an API key for Openchargemap: https://api.openchargemap.io/
URL = "https://api.openchargemap.io/v3/poi?"

API_KEY = "YOUR_API_KEY"

if API_KEY == "YOUR_API_KEY":
    raise Exception("You need to provide an API key for Openchargemap to use this example")

MAX_RESULTS = 10

ev_charger_protocol = Protocol("EVCharger")


def get_data(latitude, longitude, miles_radius) -> list or None:
    """
    Retrieves data from the open chargemap API for EV chargers.
    Args:
        latitude (float): The latitude coordinate.
        longitude (float): The longitude coordinate.
        miles_radius (float): The radius in miles for searching EV chargers.
    Returns:
        list or None: A list of EV charger data if successful, or None if the request fails.
    """
    ev_charger_url = (
            URL
            + f"maxresults={MAX_RESULTS}&latitude={latitude}&longitude={longitude}&distance={miles_radius}"
    )
    response = requests.get(url=ev_charger_url, headers={"x-api-key": API_KEY}, timeout=5)
    if response.status_code == 200:
        data = response.json()
        return data
    return []


@ev_charger_protocol.on_message(model=EvRequest, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: EvRequest):
    ctx.logger.info(f"Received message from {sender}.")
    try:
        data = get_data(msg.latitude, msg.longitude, msg.miles_radius)
        request_id = str(uuid.uuid4())
        options = []
        ctx_storage = {}
        for idx, o in enumerate(data):
            option = f"""● {o['AddressInfo']['Title']} , which is located {round(o['AddressInfo']['Distance'], 2)} miles from the location."""
            options.append(KeyValue(key=idx, value=option))
            ctx_storage[idx] = option
        ctx.storage.set(request_id, ctx_storage)
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
            await ctx.send(
                sender,
                UAgentResponse(
                    message="No ev chargers are available for this context",
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


agent.include(ev_charger_protocol)
agent.include(booking_proto())
