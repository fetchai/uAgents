from uagents import Agent, Context

agent = Agent(name="alice")


@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {ctx.name} and my address is {ctx.address}.")
    ctx.storage.set("count", 0)

@agent.on_event("shutdown")
async def goodbye(ctx: Context):
    ctx.logger.info("Agent process finished!")


@agent.on_interval(period=2.0)
async def counter(ctx: Context):
    current_count = ctx.storage.get("count")
    ctx.logger.info(f"My count is: {current_count}")
    ctx.storage.set("count", current_count + 1)


if __name__ == "__main__":
    agent.run()
