from uagents import Agent, Context, Model
from tortoise import Tortoise
from models import Availability, RoomRequest, RoomResponse


HOTEL_SEED = "put_hotel_seed_phrase_here"

hotel = Agent(
    name="hotel",
    port=8001,
    seed=HOTEL_SEED ,
    endpoint=["http://127.0.0.1:8001/submit"],
)

@hotel.on_event("startup")
async def startup(_ctx: Context):
    await Tortoise.init(
        db_url="sqlite://db.sqlite3", modules={"models": ["models"]}
    )
    await Tortoise.generate_schemas()

    await Availability.create(
        room_available=True,
        min_price=50,
    )


@hotel.on_event("shutdown")
async def shutdown(_ctx: Context):
    await Tortoise.close_connections()

@hotel.on_message(model=RoomRequest)
async def message_handler(ctx: Context, sender: str, msg: RoomRequest):
    availability = await Availability.first()
    success = False
    if availability.room_available:
        ctx.logger.info(f"Room available, attempting to book")
        if availability.min_price <= msg.max_price:
            success = True
            ctx.logger.info(f"Offer of ${msg.max_price} accepted!")
            availability.room_available = False
            await availability.save()
        else:
            ctx.logger.info(f"Offer of ${msg.max_price} was to low, won't accept ")
    else:
        ctx.logger.info(f"Room unavailable")

    await ctx.send(sender, RoomResponse(success=success))


if __name__ == "__main__":
    hotel.run()
