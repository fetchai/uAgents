from uagents import Model, Protocol


class Request(Model):
    pass


class Response(Model):
    message: str


proto = Protocol(name="hello_protocol", version="1.0")


@proto.on_message(model=Request, replies=Response)
async def handle_request(ctx, sender: str, _msg: Request):
    await ctx.send(sender, Response(message=f"Hello from {ctx.name}"))
