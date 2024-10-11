from uagents import Context
from uagents.experimental.mobility import MobilityAgent as Agent
from uagents.experimental.mobility.protocols import base_protocol
from uagents.experimental.search import search_agents_by_text

vehicle_agent = Agent(
    name="My vehicle agent",
    seed="test vehicle agent #1",
    metadata={
        "mobility_type": "vehicle",
        "geolocation": {
            "latitude": 0,
            "longitude": 0,
            "radius": 1,
        },
    },
)


current_active_eois = {}
proto = base_protocol.mobility_base_protocol


@proto.on_message(model=base_protocol.CheckIn, replies=base_protocol.CheckInResponse)
async def handle_checkin(ctx: Context, sender: str, msg: base_protocol.CheckIn):
    # never gonna be triggered here
    pass


@proto.on_message(model=base_protocol.CheckInResponse, replies=set())
async def handle_checkin_response(
    ctx: Context, sender: str, msg: base_protocol.CheckInResponse
):
    ctx.logger.info(
        f"checked in with agent of type {msg.mobility_type}. Signal: {msg.signal}"
    )
    current_active_eois[sender] = msg
    # TODO update when leaving


@proto.on_message(
    model=base_protocol.StatusUpdate, replies=base_protocol.StatusUpdateResponse
)
async def handle_status_update(
    ctx: Context, sender: str, msg: base_protocol.StatusUpdateResponse
):
    known_agent = vehicle_agent.proximity_agents[sender]
    if not known_agent:
        ctx.logger.info("got status update from agent out of reach")
    else:
        ctx.logger.info(f"new signal from {known_agent["name"]}: {msg.signal}")


vehicle_agent.include(proto)


@vehicle_agent.on_event("startup")
def startup(ctx: Context):
    # test the search api
    resp = search_agents_by_text("any agents out there?")
    ctx.logger.info(f"search results: {resp}")


if __name__ == "__main__":
    vehicle_agent.run()
