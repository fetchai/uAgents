from uagents import Agent, Model, Protocol

BOB_SEED = "put_bobs_seed_phrase_here"

bob = Agent(
    name="bob",
    port=8001,
    seed=BOB_SEED,
    endpoint=["http://127.0.0.1:8001/submit"],
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


bob.include(proto)

if __name__ == "__main__":
    bob.run()
