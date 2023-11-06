from datetime import datetime
from pytz import utc

from tortoise import Tortoise

from protocols.cleaning import cleaning_proto
from protocols.cleaning.models import Availability, Provider, Service, ServiceType

from uagents import Agent, Context


cleaner = Agent(
    name="cleaner",
    port=8001,
    seed="cleaner secret phrase",
    endpoint={
        "http://127.0.0.1:8001/submit": {},
    },
)


# build the cleaning service agent from the cleaning protocol
cleaner.include(cleaning_proto)


@cleaner.on_event("startup")
async def startup(_ctx: Context):
    await Tortoise.init(
        db_url="sqlite://db.sqlite3", modules={"models": ["protocols.cleaning.models"]}
    )
    await Tortoise.generate_schemas()

    provider = await Provider.create(name=cleaner.name, location="London Kings Cross")

    floor = await Service.create(type=ServiceType.FLOOR)
    window = await Service.create(type=ServiceType.WINDOW)
    laundry = await Service.create(type=ServiceType.LAUNDRY)

    await provider.services.add(floor)
    await provider.services.add(window)
    await provider.services.add(laundry)

    await Availability.create(
        provider=provider,
        time_start=utc.localize(datetime.fromisoformat("2022-01-31 00:00:00")),
        time_end=utc.localize(datetime.fromisoformat("2023-05-01 00:00:00")),
        max_distance=10,
        min_hourly_price=5,
    )


@cleaner.on_event("shutdown")
async def shutdown(_ctx: Context):
    await Tortoise.close_connections()


if __name__ == "__main__":
    cleaner.run()
