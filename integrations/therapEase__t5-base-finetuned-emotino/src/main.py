# develop a meet scheduling agent using uagents librarry
from uagents import Agent, Bureau, Context, Model

greeshma = Agent("Greeshma", seed="Greeshma knows konkani")


@greeshma.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("Hi, Its started")
    # await ctx.send(greeshma.address, meet_model(meet_date="15/4/2024", meet_time="0"))


if __name__ == "__main__":
    greeshma.run()
