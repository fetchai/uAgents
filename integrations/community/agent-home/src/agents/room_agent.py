from uagents import Agent, Context
from uagents.setup import fund_agent_if_low


room = Agent(
    name="smart_room",
    port=8001,
    seed="room secret phrase",
    endpoint=["http://127.0.0.1:8001/submit"],
)

fund_agent_if_low(room.wallet.address())


from agents.protocols.room_protocols import light_proto, ac_proto, window_proto

# build the restaurant agent from stock protocols
room.include(light_proto)
room.include(ac_proto)
room.include(window_proto)


@room.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"{room.name} is activating !")
    ctx.storage.set("lights", 0)
    ctx.storage.set("ac", (0, 25))
    ctx.storage.set("window", (0, 0))


# print(room.address)
