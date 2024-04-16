from uagents import Agent, Context, Model, Protocol

BOB_ADDRESS = "put_bob_address_here"

ALICE_SEED = "put_alices_seed_phrase_here"

alice = Agent(
    name="alice",
    port=8000,
    seed=ALICE_SEED,
    endpoint=["http://127.0.0.1:8000/submit"],
)


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
    ctx.logger.info(
        f"agent {sender} calculated: {msg.original_number} squared is {msg.square}"
    )


alice.include(proto)


@alice.on_interval(period=10)
async def request_square(ctx: Context):
    num = 7
    ctx.logger.info(f"What is {num} squared?")
    await ctx.send(BOB_ADDRESS, Request(number=num))


if __name__ == "__main__":
    alice.run()
