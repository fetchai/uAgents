from uagents import Agent, Bureau, Context, Model, Protocol

ALICE_SEED = "put_alice_seed_here"
BOB_SEED = "put_bobs_seed_here"

alice = Agent(name="alice", seed=ALICE_SEED)
bob = Agent(name="bob", seed=BOB_SEED)

class Request(Model):
    number: int

class Response(Model):
    square: int
    original_number: int

proto = Protocol(name="square_protocol", version="1.0")

@proto.on_message(model=Request, replies=Response)
async def request_handler(ctx, sender: str, msg: Request):
    square = msg.number * msg.number
    await ctx.send(sender, Response(square=square, original_number=msg.number))

@proto.on_message(model=Response)
async def response_handler(ctx, sender: str, msg: Response):
    ctx.logger.info(f"agent {sender} calculated: {msg.original_number} squared is {msg.square}")

alice.include(proto)
bob.include(proto)

@alice.on_interval(period=10)
async def request_square(ctx: Context):
    num = 7
    ctx.logger.info(f"What is {num} squared?")
    await ctx.send(bob.address, Request(number=num))

bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == "__main__":
    bureau.run()
