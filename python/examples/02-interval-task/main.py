from uagents import Agent, Context

agent = Agent(name="alice")


@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {ctx.name} and my address is {ctx.address}.")


@agent.on_interval(period=2.0)
async def say_hello(ctx: Context):
    ctx.logger.info("Hello!")


if __name__ == "__main__":
    agent.run()
