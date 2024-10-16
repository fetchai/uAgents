from time import time

from uagents import Context
from uagents.experimental.mobility import MobilityAgent as Agent
from uagents.experimental.mobility.protocols import base_protocol
from uagents.types import AgentGeolocation

static_agent = Agent(
    name="traffic light@2.2",
    mobility_type="traffic_light",
    port=8112,
    endpoint="https://localhost:8112/submit",
    location=AgentGeolocation(latitude=3, longitude=3, radius=1),
)

proto = base_protocol.mobility_base_protocol


@proto.on_message(model=base_protocol.CheckIn, replies=base_protocol.CheckInResponse)
async def handle_checkin(ctx: Context, sender: str, msg: base_protocol.CheckIn):
    if msg.mobility_type == "vehicle":
        ctx.logger.info(f"new vehicle entered service area at {int(time())}")
    else:
        ctx.logger.info(
            f"encountered unsupported mobility agent of type {msg.mobility_type}"
        )

    static_agent.checkin_agent(sender, msg)  # TODO timeout/heartbeat?

    await ctx.send(
        sender,
        base_protocol.CheckInResponse(
            mobility_type=static_agent.mobility_type,
            signal=static_agent.storage.get("signal") or "red",
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


@proto.on_message(model=base_protocol.StatusUpdateResponse, replies=set())
async def handle_statusupdate_response(
    ctx: Context, sender: str, msg: base_protocol.StatusUpdateResponse
):
    pass


@proto.on_message(model=base_protocol.CheckOut, replies=base_protocol.CheckOutResponse)
async def handle_checkout(ctx: Context, sender: str, msg: base_protocol.CheckOut):
    static_agent.checkout_agent(sender)
    ctx.logger.info(f"{sender} said bye")


@proto.on_message(model=base_protocol.CheckOutResponse, replies=set())
async def handle_checkout_response(
    ctx: Context, sender: str, msg: base_protocol.CheckOutResponse
):
    # never gonna be triggered in this agent
    pass


static_agent.include(proto)


@static_agent.on_interval(5)
async def switch_signal(ctx: Context):
    signal = ctx.storage.get("signal") or "red"
    signal = "green" if signal == "red" else "red"
    ctx.storage.set("signal", signal)
    for addr in static_agent.checkedin_agents:
        await ctx.send(addr, base_protocol.StatusUpdate(signal=signal))


if __name__ == "__main__":
    static_agent.run()
