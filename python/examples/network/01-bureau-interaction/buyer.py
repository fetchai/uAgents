from uagents import Model, Agent, Context
import random


class OfferRequest(Model):
    offer: int


class OfferResponse(Model):
    accept: bool


BUYER_SEED = "put_buyer_seed_phrase_here"

SELLER_ADDRESSES = ["list all seller addresses here"]

buyer = Agent(
    name="buyer",
    port=8000,
    seed=BUYER_SEED,
    endpoint=["http://127.0.0.1:8000/submit"],
)

offer = 50


@buyer.on_event("startup")
async def start(ctx: Context):
    ctx.storage.set("seller_found", False)


@buyer.on_interval(period=5)
async def send_offer(ctx: Context):
    found = ctx.storage.get("seller_found")
    if not found:
        random_address = random.choice(SELLER_ADDRESSES)
        await ctx.send(random_address, OfferRequest(offer=offer))


@buyer.on_message(model=OfferResponse)
async def response_handler(ctx, sender: str, msg: OfferResponse):
    status = "Accepted" if msg.accept else "Declined"
    ctx.logger.info(f"agent {sender} : {status} offer of {offer}")
    if msg.accept:
        ctx.storage.set("seller_found", True)


if __name__ == "__main__":
    buyer.run()
