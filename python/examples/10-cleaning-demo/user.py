from datetime import datetime, timedelta
from pytz import utc

from protocols.cleaning import (
    ServiceBooking,
    BookingResponse,
    ServiceRequest,
    ServiceResponse,
)
from protocols.cleaning.models import ServiceType
from uagents import Agent, Context


CLEANER_ADDRESS = (
    "test-agent://agent1qdfdx6952trs028fxyug7elgcktam9f896ays6u9art4uaf75hwy2j9m87w"
)

user = Agent(
    name="user",
    port=8000,
    seed="cleaning user recovery phrase",
    endpoint={
        "http://127.0.0.1:8000/submit": {},
    },
)


request = ServiceRequest(
    user=user.name,
    location="London Kings Cross",
    time_start=utc.localize(datetime.fromisoformat("2023-04-10 16:00:00")),
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
        ctx.logger.info(f"Requesting cleaning service: {request}")
        await ctx.send(CLEANER_ADDRESS, request)


@user.on_message(ServiceResponse, replies=ServiceBooking)
async def handle_query_response(ctx: Context, sender: str, msg: ServiceResponse):
    markdown = ctx.storage.get("markdown")
    if msg.accept:
        ctx.logger.info("Cleaner is available, attempting to book now")
        booking = ServiceBooking(
            location=request.location,
            time_start=request.time_start,
            duration=request.duration,
            services=request.services,
            price=markdown * msg.price,
        )
        await ctx.send(sender, booking)
    else:
        ctx.logger.info("Cleaner is not available - nothing more to do")
        ctx.storage.set("completed", True)


@user.on_message(BookingResponse, replies=set())
async def handle_book_response(ctx: Context, _sender: str, msg: BookingResponse):
    if msg.success:
        ctx.logger.info("Booking was successful")
    else:
        ctx.logger.info("Booking was UNSUCCESSFUL")

    ctx.storage.set("completed", True)


if __name__ == "__main__":
    user.run()
