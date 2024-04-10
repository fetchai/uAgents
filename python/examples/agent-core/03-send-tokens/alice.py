from bob import bob
from uagents import Agent, Context, Model
from uagents.network import wait_for_tx_to_complete


class PaymentRequest(Model):
    wallet_address: str
    amount: int
    denom: str


class TransactionInfo(Model):
    tx_hash: str


AMOUNT = 100
DENOM = "atestfet"
ALICE_SEED = "put_alices_seed_phrase_here"
alice = Agent(name="alice", seed=ALICE_SEED)


@alice.on_interval(period=10.0)
async def request_funds(ctx: Context):
    await ctx.send(
        bob.address,
        PaymentRequest(
            wallet_address=str(ctx.wallet.address()), amount=AMOUNT, denom=DENOM
        ),
    )


@alice.on_message(model=TransactionInfo)
async def transaction_handler(ctx: Context, sender: str, msg: TransactionInfo):
    ctx.logger.info(f"Received transaction info from {sender}: {msg}")
    tx_resp = await wait_for_tx_to_complete(msg.tx_hash, ctx.ledger)

    coin_received = tx_resp.events["coin_received"]
    if (
        coin_received["receiver"] == str(ctx.wallet.address())
        and coin_received["amount"] == f"{AMOUNT}{DENOM}"
    ):
        ctx.logger.info(f"Transaction was successful: {coin_received}")
