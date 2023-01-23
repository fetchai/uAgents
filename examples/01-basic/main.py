from uagents import Agent, Context

agent = Agent()


@agent.on_interval(period=1.0)
async def on_interval1(_ctx: Context):
    print("User interval code 1")


@agent.on_interval(period=3.0)
async def on_interval2(_ctx: Context):
    print("User interval code 3")


if __name__ == "__main__":
    agent.run()
