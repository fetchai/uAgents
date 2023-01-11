from datetime import datetime
from pytz import utc

from tortoise import Tortoise

from protocols.cleaning import cleaning_proto
from protocols.cleaning.models import Availability, Provider, Service, ServiceType

from nexus import Agent
from nexus.setup import fund_agent_if_low


cleaner = Agent(
    name="cleaner",
    port=8001,
    seed="cleaner secret seed phrase",
    endpoint="http://127.0.0.1:8001/submit",
)

fund_agent_if_low(cleaner.wallet.address())

print("Agent address:", cleaner.address)

# build the cleaning service agent from the cleaning protocol
cleaner.include(cleaning_proto)


@cleaner.on_event("startup")
async def startup():
    await Tortoise.init(
        db_url="sqlite://db.sqlite3", modules={"models": ["protocols.cleaning.models"]}
    )
    await Tortoise.generate_schemas()

    provider = await Provider.create(name=cleaner.name, address=12)

    floor = await Service.create(type=ServiceType.FLOOR)
    window = await Service.create(type=ServiceType.WINDOW)
    laundry = await Service.create(type=ServiceType.LAUNDRY)

    await provider.services.add(floor)
    await provider.services.add(window)
    await provider.services.add(laundry)

    await Availability.create(
        provider=provider,
        time_start=utc.localize(datetime.fromisoformat("2022-12-31 10:00:00")),
        time_end=utc.localize(datetime.fromisoformat("2022-12-31 22:00:00")),
        max_distance=10,
        min_hourly_price=5,
    )


@cleaner.on_event("shutdown")
async def shutdown():
    await Tortoise.close_connections()


if __name__ == "__main__":
    cleaner.run()
