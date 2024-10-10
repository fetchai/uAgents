from uagents import Context
from uagents.experimental.mobility import MobilityAgent as Agent
from uagents.experimental.mobility.protocol import base_protocol
from uagents.experimental.search import search_agents_by_text
from uagents.types import AgentGeoLocation

vehicle_agent = Agent(
    name="My vehicle agent",
    mobility_type="traffic_lights",
    location=AgentGeoLocation(lat=0, lng=0, radius=1),
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


vehicle_agent.include(proto)


@vehicle_agent.on_event("startup")
def startup(ctx: Context):
    # test the search api
    resp = search_agents_by_text("any agents out there?")
    ctx.logger.info(f"search results: {resp}")


if __name__ == "__main__":
    vehicle_agent.run()
