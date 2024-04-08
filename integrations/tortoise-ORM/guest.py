from uagents import Agent, Context
from models import RoomRequest, RoomResponse

HOTEL_ADDRESS = "agent1qvsmzq0awkv0mptpuw4fgr4a4fqqdejsxuju4auk08aqmq98hzuhgcgfspp"
GUEST_SEED = "put_guest_seed_phrase_here"

guest = Agent(
    name="guest",
    port=8000,
    seed=GUEST_SEED,
    endpoint=["http://127.0.0.1:8000/submit"],
)

request = RoomRequest(max_price=70)

@guest.on_event("startup")
async def startup(ctx: Context):
    ctx.storage.set("completed", False)

@guest.on_interval(period=8.0)
async def send_message(ctx: Context):

    completed = ctx.storage.get("completed")

    if not completed:
        ctx.logger.info(f"Sending room booking request: {request}")
        await ctx.send(HOTEL_ADDRESS, request)


@guest.on_message(RoomResponse, replies=set())
async def booking_handler(ctx: Context, _sender: str, msg: RoomResponse):
    if msg.success:
        ctx.logger.info("Booking was successful")
    else:
        ctx.logger.info("Booking was unsuccessful")

    ctx.storage.set("completed", True)


if __name__ == "__main__":
    guest.run()
