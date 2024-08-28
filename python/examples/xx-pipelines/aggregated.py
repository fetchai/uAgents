import random

from uagents import Agent, Model, Bureau, Context, Protocol
from uagents.experimental.pipelines import Pipeline


class RandomNumberRequest(Model):
    pass


class RandomNumberResponse(Model):
    value: float


rng_proto = Protocol()


@rng_proto.on_message(RandomNumberRequest, replies={RandomNumberResponse})
async def handle_rng_request(ctx: Context, sender: str, msg: RandomNumberRequest):
    await ctx.send(sender, RandomNumberResponse(value=random.random()))


agent1 = Agent(name="rng-source-1")
agent2 = Agent(name="rng-source-2")
agent3 = Agent(name="rng-source-3")
agent4 = Agent(name="rng-aggregator")

agent1.include(rng_proto)
agent2.include(rng_proto)
agent3.include(rng_proto)

# TODO(EJF): This would not be necessary in the future, the user would just call the scatter_gather method
# For the moment, we create a pipeline that semantically represents the scatter-gather pattern that we are looking for
pipeline = Pipeline.first([
    (agent1.address, RandomNumberRequest, RandomNumberResponse),
    (agent2.address, RandomNumberRequest, RandomNumberResponse),
    (agent3.address, RandomNumberRequest, RandomNumberResponse),
])


@agent4.on_interval(period=10)
async def periodically(ctx: Context):

    # send the requests and collect the responses
    responses = await pipeline.scatter_and_gather(ctx, [
        (agent1.address, RandomNumberRequest()),
        (agent2.address, RandomNumberRequest()),
        (agent3.address, RandomNumberRequest()),
    ])

    # build the final result from summing all the non-None responses
    rng_values = list(
        map(
            lambda x: x[1].value,
            filter(
                lambda x: x is not None,
                responses
            )
        )
    )
    assert len(rng_values) > 0, "No RNG values received"
    final_rng = sum(rng_values) / len(rng_values)

    ctx.logger.info(f"Final RNG: {ctx.session} -> {final_rng}")


@agent4.on_message(RandomNumberResponse)
async def handle_rng_response(ctx: Context, sender: str, msg: RandomNumberResponse):
    # TODO(EJF): Ideally the user should not have to call this method or set this up, inside the scatter_gather method
    #            we would register a middleware that would handle this for us.
    await pipeline.handle(ctx, sender, msg)


bureau = Bureau()
bureau.add(agent1)
bureau.add(agent2)
bureau.add(agent3)
bureau.add(agent4)


if __name__ == '__main__':
    bureau.run()