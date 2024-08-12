import random

from uagents import Agent, Bureau, Context, Model
from uagents.experimental.pipelines import SimpleAgentChain


class TemperatureRequest(Model):
    pass


class TemperatureResponse(Model):
    temperature_celsius: float
    temperature_fahrenheit: float


class FahrenheitTemperatureRequest(Model):
    pass


class FahrenheitTemperatureResponse(Model):
    temperature: float


agent1 = Agent(name="agent1")
agent2 = Agent(name="agent2")
agent3 = Agent(name="agent3")


agent2_chain = SimpleAgentChain(
    agent3.address, FahrenheitTemperatureRequest, TemperatureResponse
)


@agent1.on_interval(period=10)
async def startup(ctx: Context):
    ctx.logger.info("Sending temperature request")
    await ctx.send(agent2.address, TemperatureRequest())


@agent2.on_message(TemperatureRequest)
async def handle_temperature_request(
    ctx: Context, sender: str, msg: TemperatureRequest
):
    ctx.logger.info("Received temperature request")

    await agent2_chain.request(ctx, sender, FahrenheitTemperatureRequest())


@agent3.on_message(FahrenheitTemperatureRequest)
async def handle_fahrenheit_temperature_request(
    ctx: Context, sender: str, msg: TemperatureRequest
):
    ctx.logger.info("Received fahrenheit temperature request")

    # generate a random plausible temperature in fahrenheit
    temperature = ((random.random() * 5.0) - 2.5) + 88.0

    await ctx.send(sender, FahrenheitTemperatureResponse(temperature=temperature))


@agent2.on_message(FahrenheitTemperatureResponse)
async def handle_fahrenheit_temperature_response(
    ctx: Context, sender: str, msg: FahrenheitTemperatureResponse
):
    ctx.logger.info(f"Received fahrenheit temperature response: {msg}")

    # convert the temperature to Celsius
    celsius = (msg.temperature - 32) * (5 / 9)

    # build the response
    msg = TemperatureResponse(
        temperature_celsius=celsius, temperature_fahrenheit=msg.temperature
    )

    # send the response back
    await agent2_chain.respond(ctx, msg)


@agent1.on_message(TemperatureResponse)
async def handle_temperature_response(
    ctx: Context, sender: str, msg: TemperatureResponse
):
    ctx.logger.info(f"Received temperature response: {msg}")


bureau = Bureau()
bureau.add(agent1)
bureau.add(agent2)
bureau.add(agent3)


if __name__ == "__main__":
    bureau.run()
