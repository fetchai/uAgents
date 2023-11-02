from uagents import Agent, Bureau, Context, Model, Protocol

# create agents
# alice and bob will support the protocol
# charles will try to reach all agents supporting the protocol
alice = Agent(name="alice", seed="alice recovery phrase")
bob = Agent(name="bob", seed="bob recovery phrase")
charles = Agent(name="charles", seed="charles recovery phrase")


class BroadcastExampleRequest(Model):
    pass


class BroadcastExampleResponse(Model):
    text: str


# define protocol
proto = Protocol(name="proto", version="1.0")


@proto.on_message(model=BroadcastExampleRequest, replies=BroadcastExampleResponse)
async def handle_request(ctx: Context, sender: str, _msg: BroadcastExampleRequest):
    await ctx.send(sender, BroadcastExampleResponse(text=f"Hello from {ctx.name}"))


# include protocol
# Note: after the first registration on the almanac smart contract, it will
# take about 5 minutes before the agents can be found through the protocol
alice.include(proto)
bob.include(proto)


# let charles send the message to all agents supporting the protocol
@charles.on_interval(period=5)
async def say_hello(ctx: Context):
    await ctx.experimental_broadcast(proto.digest, message=BroadcastExampleRequest())


@charles.on_message(model=BroadcastExampleResponse)
async def handle_response(ctx: Context, sender: str, msg: BroadcastExampleResponse):
    ctx.logger.info(f"Received response from {sender}: {msg.text}")


bureau = Bureau(port=8000, endpoint="http://localhost:8000/submit")
bureau.add(alice)
bureau.add(bob)
bureau.add(charles)


if __name__ == "__main__":
    bureau.run()
