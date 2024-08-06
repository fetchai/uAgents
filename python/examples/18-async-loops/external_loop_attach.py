import asyncio
import contextlib

from uagents import Agent, Bureau, Context

loop = asyncio.get_event_loop()


agent = Agent(
    name="looper",
    seed="<YOUR_SEED>",
)

bureau = Bureau(
    agents=[agent],
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
    print("Attaching the agent or bureau to the external loop...")
    loop.create_task(coro())

    # > when attaching the agent to the external loop
    loop.create_task(agent.run_async())

    # > when attaching a bureau to the external loop
    # loop.create_task(bureau.run_async())

    with contextlib.suppress(KeyboardInterrupt):
        loop.run_forever()
