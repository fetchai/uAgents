from uagents import Model, Protocol


class OfferRequest(Model):
    offer: int


class OfferResponse(Model):
    accept: bool


proto = Protocol(name="seller_protocol", version="1.0")


@proto.on_message(model=OfferRequest, replies=OfferResponse)
async def request_handler(ctx, sender: str, msg: OfferRequest):
    min_price = ctx.storage.get("min_price")
    accept = msg.offer >= min_price
    await ctx.send(sender, OfferResponse(accept=accept))
