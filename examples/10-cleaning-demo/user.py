from datetime import datetime, timedelta
from pytz import utc

from protocols.cleaning import (
    ServiceBooking,
    BookingResponse,
    ServiceRequest,
    ServiceResponse,
)
from protocols.cleaning.models import ServiceType
from nexus import Agent, Context
from nexus.setup import fund_agent_if_low


CLEANER_ADDRESS = "agent1q0g3v3masp6fg2dpfxtfxu9ysuzeusgpdmcz5whv30jm7m7u2vt2zms6p2z"

user = Agent(
    name="user",
    port=8000,
    seed="user secret seed phrase",
    endpoint="http://127.0.0.1:8000/submit",
)

fund_agent_if_low(user.wallet.address())

request = ServiceRequest(
    user=user.name,
    location="London Kings Cross",
    time_start=utc.localize(datetime.fromisoformat("2023-01-10 16:00:00")),
    duration=timedelta(hours=4),
    services=[ServiceType.WINDOW, ServiceType.LAUNDRY],
    max_price=60,
)

MARKDOWN = 0.8


@user.on_interval(period=3.0, messages=ServiceRequest)
async def interval(ctx: Context):
    ctx.storage.set("markdown", MARKDOWN)
    completed = ctx.storage.get("completed")

    if not completed:
        print(f"Requesting cleaning service: {request}")
        await ctx.send(CLEANER_ADDRESS, request)


@user.on_message(ServiceResponse, replies=ServiceBooking)
async def handle_query_response(ctx: Context, sender: str, msg: ServiceResponse):
    markdown = ctx.storage.get("markdown")
    if msg.accept:
        print("Cleaner is available, attempting to book now")
        booking = ServiceBooking(
            location=request.location,
            time_start=request.time_start,
            duration=request.duration,
            services=request.services,
            price=markdown * msg.price,
        )
        await ctx.send(sender, booking)
    else:
        print("Cleaner is not available - nothing more to do")
        ctx.storage.set("completed", True)


@user.on_message(BookingResponse, replies=set())
async def handle_book_response(ctx: Context, _sender: str, msg: BookingResponse):
    if msg.success:
        print("Booking was successful")
    else:
        print("Booking was UNSUCCESSFUL")

    ctx.storage.set("completed", True)


if __name__ == "__main__":
    user.run()
