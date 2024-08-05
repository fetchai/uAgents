import asyncio

from uagents import Agent, Bureau, Context

loop = asyncio.get_event_loop()


agent = Agent(
    name="looper",
    seed="<YOUR_SEED>",
    loop=loop,
)

bureau = Bureau(
    agents=[agent],
    loop=loop,
)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(">>> Looper is starting up.")


@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    ctx.logger.info(">>> Looper is shutting down.")


async def coro():
    while True:
        print("doing hard work...")
        await asyncio.sleep(1)


if __name__ == "__main__":
    print("Starting the external loop from the agent or bureau...")
    loop.create_task(coro())

    # > when starting the external loop from the agent
    agent.run()

    # > when starting the external loop from the bureau
    # bureau.run()
