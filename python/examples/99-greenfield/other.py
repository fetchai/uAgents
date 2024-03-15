from uagents import Agent, Context, Model

agent = Agent(
    name="other_agent",
    seed="f78zr78436784hf8wcrtz718nnvhdusifncmfmch43iuty0bzc77ewt9nbv8z7",
    port=8081,
    endpoint="http://localhost:8081/submit",
)


class Message(Model):
    pass


@agent.on_interval(1)
async def interval_handler(ctx: Context):
    await ctx.send(
        "agent1qwhqseh0ap9akj0z633xvfmccfzvpqx6c8z73f562x357l3cu6dc5tvmsdv",
        message=Message(),
    )


agent.run()
