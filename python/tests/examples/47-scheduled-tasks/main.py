from uagents import Agent, Context

agent = Agent(name="scheduler")


@agent.on_schedule("* * * * *")
async def every_minute(ctx: Context):
    ctx.logger.info("Running every minute (UTC).")


@agent.on_schedule("*/5 9-17 * * MON-FRI", tz="Europe/London")
async def office_hours(ctx: Context):
    ctx.logger.info("Running every 5 minutes during London office hours.")


@agent.on_interval(period=30.0)
async def every_30_seconds(ctx: Context):
    ctx.logger.info("Running every 30 seconds.")


if __name__ == "__main__":
    agent.run()
