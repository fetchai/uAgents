from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low


class PaymentRequest(Model):
    wallet_address: str
    amount: int
    denom: str


class TransactionInfo(Model):
    tx_hash: str


AMOUNT = 100
BOB_SEED = "put_bobs_seed_phrase_here"
bob = Agent(name="bob", seed=BOB_SEED)


fund_agent_if_low(bob.wallet.address(), min_balance=AMOUNT)


@bob.on_message(model=PaymentRequest, replies=TransactionInfo)
async def payment_handler(ctx: Context, sender: str, msg: PaymentRequest):
    ctx.logger.info(f"Received payment request from {sender}: {msg}")

    transaction = ctx.ledger.send_tokens(
        msg.wallet_address, msg.amount, msg.denom, ctx.wallet
    )

    await ctx.send(sender, TransactionInfo(tx_hash=transaction.tx_hash))
