import os
import uuid

import requests
from messages import EVRequest, KeyValue, UAgentResponse, UAgentResponseType
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low

EV_SEED = os.getenv("EV_SEED", "ev charger service secret phrase")

agent = Agent(
    name="ev_adaptor",
    seed=EV_SEED,
)

fund_agent_if_low(agent.wallet.address())

OPENCHARGEMAP_API_KEY = os.environ.get("OPENCHARGEMAP_API_KEY", "")

assert (
    OPENCHARGEMAP_API_KEY
), "OPENCHARGEMAP_API_KEY environment variable is missing from .env"

OPENCHARGEMAP_API_URL = "https://api.openchargemap.io/v3/poi?"
MAX_RESULTS = 100


def get_ev_chargers(latitude: float, longitude: float, miles_radius: float) -> list:
    """Return ev chargers available within given miles_readius of the latiture and longitude.
    this information is being retrieved from https://api.openchargemap.io/v3/poi? API
    """
    response = requests.get(
        url=OPENCHARGEMAP_API_URL
        + f"maxresults={MAX_RESULTS}&latitude={latitude}&longitude={longitude}&distance={miles_radius}",
        headers={"x-api-key": OPENCHARGEMAP_API_KEY},
        timeout=5,
    )
    if response.status_code == 200:
        return response.json()
    return []


ev_chargers_protocol = Protocol("EvChargers")


@ev_chargers_protocol.on_message(model=EVRequest, replies=UAgentResponse)
async def ev_chargers(ctx: Context, sender: str, msg: EVRequest):
    ctx.logger.info(f"Received message from {sender}")
    try:
        ev_chargers = get_ev_chargers(msg.latitude, msg.longitude, msg.miles_radius)
        request_id = str(uuid.uuid4())
        conn_types = []
        options = []
        for idx, ev_station in enumerate(ev_chargers):
            for conn in ev_station["Connections"]:
                conn_types.append(conn["ConnectionType"]["Title"])
                conn_type_str = ", ".join(conn_types)
                option = f"""● EV charger: {ev_station['AddressInfo']['Title']} , located {round(ev_station['AddressInfo']['Distance'], 2)} miles from your location\n● Usage cost {ev_station['UsageCost']};\n● Type - {conn_type_str}"""

            options.append(KeyValue(key=idx, value=option))
        await ctx.send(
            sender,
            UAgentResponse(
                options=options,
                type=UAgentResponseType.SELECT_FROM_OPTIONS,
                request_id=request_id,
            ),
        )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR)
        )


agent.include(ev_chargers_protocol)
