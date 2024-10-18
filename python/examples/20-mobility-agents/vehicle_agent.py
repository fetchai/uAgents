from uagents import Context
from uagents.experimental.mobility import MobilityAgent as Agent
from uagents.experimental.mobility.protocols import base_protocol
from uagents.experimental.search import geosearch_agents_by_proximity
from uagents.types import AgentGeolocation

vehicle_agent = Agent(
    name="My vehicle agent",
    seed="test vehicle agent #1",
    mobility_type="vehicle",
    port=8111,
    endpoint="http://localhost:8111/submit",
    location=AgentGeolocation(
        latitude=52.506926,
        longitude=13.377207,
        radius=2,
    ),
)


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


@proto.on_message(
    model=base_protocol.StatusUpdate, replies=base_protocol.StatusUpdateResponse
)
async def handle_status_update(
    ctx: Context, sender: str, msg: base_protocol.StatusUpdate
):
    known_agent = next(
        (a for a in vehicle_agent.proximity_agents if a.address == sender), None
    )
    if not known_agent:
        ctx.logger.info("Got status update from agent out of reach")
    else:
        ctx.logger.info(f"New signal from {known_agent.address[:10]}...: {msg.signal}")


@proto.on_message(model=base_protocol.CheckOut, replies=base_protocol.CheckOutResponse)
async def handle_checkout(ctx: Context, sender: str, msg: base_protocol.CheckOut):
    pass


@proto.on_message(model=base_protocol.CheckOutResponse, replies=set())
async def handle_checkout_response(
    ctx: Context, sender: str, msg: base_protocol.CheckOutResponse
):
    ctx.logger.info(f"famous last words: {msg.receipt}")


vehicle_agent.include(proto)


@vehicle_agent.on_event("startup")
async def startup(ctx: Context):
    current_location = (
        vehicle_agent.location["latitude"],
        vehicle_agent.location["longitude"],
    )
    ctx.logger.info(f"Vehicle agent ready at {current_location}")
    # test the search api
    proximity_agents = geosearch_agents_by_proximity(
        vehicle_agent.location["latitude"],
        vehicle_agent.location["longitude"],
        vehicle_agent.location["radius"],
        30,
    )
    filtered_agents = [
        a for a in proximity_agents if a.address != vehicle_agent.address
    ]
    ctx.logger.info(f"There are currently {len(filtered_agents)} agents nearby.")


if __name__ == "__main__":
    print(vehicle_agent.address)
    vehicle_agent.run()
