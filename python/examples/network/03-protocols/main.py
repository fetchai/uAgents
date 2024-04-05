from uagents import Agent, Bureau, Context
from protocol.protocol import proto, Request, Response


ALICE_SEED = "put_alices_seed_here"
BOB_SEED = "put_bobs_seed_here"
CHARLES_SEED = "put_charlys_seed_here"

alice = Agent(name="alice", seed=ALICE_SEED)
bob = Agent(name="bob", seed=BOB_SEED)
charles = Agent(name="charles", seed=CHARLES_SEED)


alice.include(proto)
bob.include(proto)

print(proto.digest)


@charles.on_interval(period=10)
async def say_hello(ctx: Context):
    await ctx.broadcast(proto.digest, message=Request())


@charles.on_message(model=Response)
async def handle_response(ctx: Context, sender: str, msg: Response):
    ctx.logger.info(f"Received response from {sender}: {msg.message}")


bureau = Bureau(port=8000, endpoint="http://localhost:8000/submit")
bureau.add(alice)
bureau.add(bob)
bureau.add(charles)

if __name__ == "__main__":
    bureau.run()
