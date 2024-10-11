from datetime import time

from uagents import Context
from uagents.experimental.mobility import MobilityAgent as Agent
from uagents.experimental.mobility.protocol import base_protocol

static_agent = Agent(
    name="traffic light@2.2",
    metadata={
        "mobility_type": "traffic_lights",
        "geolocation": {
            "latitude": 2,
            "longitude": 2,
            "radius": 1,
        },
    },
)


signal = "red"
current_checkedin_vehicles = {}
proto = base_protocol.mobility_base_protocol


@proto.on_message(model=base_protocol.CheckIn, replies=base_protocol.CheckInResponse)
async def handle_checkin(ctx: Context, sender: str, msg: base_protocol.CheckIn):
    if msg.mobility_type == "vehicle":
        ctx.logger.info(f"new vehicle entered service area at {time.now()}")
    else:
        ctx.logger.info(
            f"encountered unsupported mobility agent of type {msg.mobility_type}"
        )
    current_checkedin_vehicles[sender] = msg  # TODO update on checkout or timeout

    await ctx.send(
        sender,
        base_protocol.CheckInResponse(
            mobility_type=static_agent.mobility_type,
            signal=signal,
            description="Traffic lights. Be wary, the yellow bulb isn't working",
        ),
    )


@proto.on_message(model=base_protocol.CheckInResponse, replies=set())
async def handle_checkin_response(
    ctx: Context, sender: str, msg: base_protocol.CheckInResponse
):
    # never gonna be triggered in this agent
    pass


@proto.on_message(
    model=base_protocol.StatusUpdate, replies=base_protocol.StatusUpdateResponse
)
async def handle_status_update(
    ctx: Context, sender: str, msg: base_protocol.StatusUpdateResponse
):
    # never gonna be triggered in this agent
    pass


static_agent.include(proto)


@static_agent.on_interval(5)
async def switch_signal(ctx: Context):
    if not signal:
        signal = "red"
    signal = "green" if signal == "red" else "red"
    for addr in current_checkedin_vehicles:
        await ctx.send(addr, base_protocol.StatusUpdate(signal=signal))


if __name__ == "__main__":
    static_agent.run()