from datetime import datetime

from uagents import Context
from uagents.experimental.mobility import MobilityAgent as Agent
from uagents.experimental.mobility.protocols import base_protocol
from uagents.types import AgentGeolocation

static_agent = Agent(
    name="roadworks",
    mobility_type="roadworks",
    port=8113,
    endpoint="http://localhost:8113/submit",
    location=AgentGeolocation(
        latitude=52.507674,
        longitude=13.378124,
        radius=15,
    ),
)

proto = base_protocol.mobility_base_protocol


@proto.on_message(model=base_protocol.CheckIn, replies=base_protocol.CheckInResponse)
async def handle_checkin(ctx: Context, sender: str, msg: base_protocol.CheckIn):
    if msg.mobility_type == "vehicle":
        ctx.logger.info(
            f"New vehicle entered service area at {datetime.now()}: {sender[:10]}..."
        )
    else:
        ctx.logger.info(
            f"Encountered unsupported mobility agent of type {msg.mobility_type}"
        )

    static_agent.checkin_agent(sender, msg)  # TODO timeout/heartbeat?

    await ctx.send(
        sender,
        base_protocol.CheckInResponse(
            mobility_type=static_agent.mobility_type,
            signal="road blocked, please take a detour",
            description="Roadworks on Stresemannstraße 124",
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
    ctx.logger.info(f"Agent {sender[:10]}... exited service area.")


@proto.on_message(model=base_protocol.CheckOutResponse, replies=set())
async def handle_checkout_response(
    ctx: Context, sender: str, msg: base_protocol.CheckOutResponse
):
    # never gonna be triggered in this agent
    pass


static_agent.include(proto)


@static_agent.on_event("startup")
async def startup(ctx: Context):
    current_location = (
        static_agent.location["latitude"],
        static_agent.location["longitude"],
    )
    ctx.logger.info(f"Roadworks agent ready at {current_location}")


if __name__ == "__main__":
    print(static_agent.address)
    static_agent.run()
