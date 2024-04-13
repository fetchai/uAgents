from uagents import Agent, Context, Model


class PaymentRequest(Model):
    wallet_address: str
    amount: int
    denom: str


class TransactionInfo(Model):
    tx_hash: str


AMOUNT = 100
DENOM = "atestfet"
ALICE_SEED = "put_alices_seed_phrase_here"
BOB_ADDRESS = "put_bob_address_here"

alice = Agent(
    name="alice",
    port=8000,
    seed=ALICE_SEED,
    endpoint=["http://127.0.0.1:8000/submit"],
)



@alice.on_interval(period=10.0)
async def request_funds(ctx: Context):
    await ctx.send(
        BOB_ADDRESS,
        PaymentRequest(
            wallet_address=str(ctx.wallet.address()), amount=AMOUNT, denom=DENOM
        ),
    )


@alice.on_message(model=TransactionInfo)
async def transaction_handler(ctx: Context, sender: str, msg: TransactionInfo):
    ctx.logger.info(f"Received transaction info from {sender}: {msg}")

    try:
        tx_resp = ctx.ledger.query_tx(msg.tx_hash)
        coin_received = tx_resp.events["coin_received"]

        if (
            coin_received["receiver"] == str(ctx.wallet.address())
            and coin_received["amount"] == f"{AMOUNT}{DENOM}"
        ):
            ctx.logger.info(f"Transaction {msg.tx_hash} was successful: {coin_received}")

        else:
            ctx.logger.info(f"Transaction {msg.tx_hash} was NOT successful")

    except:
        ctx.logger.info(f"There was an error while attempting to confirm the transaction.")

if __name__ == "__main__":
    alice.run()