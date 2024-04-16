from uagents import Agent, Context, Model


class PaymentRequest(Model):
    wallet_address: str
    amount: int
    denom: str


class TransactionInfo(Model):
    tx_hash: str


BOB_SEED = "put_bobs_seed_phrase_here"

bob = Agent(
    name="bob",
    port=8001,
    seed=BOB_SEED,
    endpoint=["http://127.0.0.1:8001/submit"],
)


@bob.on_message(model=PaymentRequest, replies=TransactionInfo)
async def payment_handler(ctx: Context, sender: str, msg: PaymentRequest):
    ctx.logger.info(f"Received payment request from {sender}: {msg}")

    transaction = ctx.ledger.send_tokens(
        msg.wallet_address, msg.amount, msg.denom, ctx.wallet
    ).wait_to_complete()

    await ctx.send(sender, TransactionInfo(tx_hash=transaction.tx_hash))

if __name__ == "__main__":
    bob.run()
