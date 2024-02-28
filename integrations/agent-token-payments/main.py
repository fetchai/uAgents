from uagents import Agent, Bureau, Context, Model
from uagents.setup import fund_agent_if_low


class PaymentRequest(Model):
    address: str
    amount: int


alice = Agent(name='alice', seed='alice token payment seed phrase')


@alice.on_interval(2)
async def alice_interval(ctx: Context):
    current_balance = ctx.ledger.query_bank_all_balances(ctx.wallet.address())[0].amount
    ctx.logger.info(f'Current balance is {current_balance}')


@alice.on_message(PaymentRequest)
async def alice_payment_request(ctx: Context, sender: str, msg: PaymentRequest):
    ctx.logger.info(f'Payment request received from {sender} to transfer {msg.amount} to {msg.address}')

    tx = ctx.ledger.send_tokens(
        msg.address,
        msg.amount,
        ctx.ledger.network_config.fee_denomination,
        ctx.wallet,
    )

    ctx.logger.info(f'Sent transaction: {tx.tx_hash} to network... waiting for confirmation')
    tx.wait_to_complete()
    ctx.logger.info(f'Transaction complete!')


bob = Agent(name='bob', seed='bob token payment seed phrase')


@bob.on_interval(2)
async def bob_interval(ctx: Context):
    current_balance = ctx.ledger.query_bank_all_balances(ctx.wallet.address())[0].amount
    ctx.logger.info(f'Current balance is {current_balance}')


@bob.on_interval(30)
async def bob_interval(ctx: Context):
    ctx.logger.info(f'Requesting payment from alice...')

    # request funds from alice
    await ctx.send(alice.address, PaymentRequest(address=str(bob.wallet.address()), amount=15))


print('Alice Address:', alice.address)
print('Alice Wallet Address:', alice.wallet.address())
print('Bob Address:', bob.address)
print('Bob Wallet Address:', bob.wallet.address())

bureau = Bureau()
bureau.add(alice)
bureau.add(bob)

if __name__ == '__main__':
    print('Funding agents (if necessary)...')
    # fund_agent_if_low(alice.wallet.address())
    # fund_agent_if_low(bob.wallet.address())

    print('Starting agents...')
    bureau.run()
