from cosmpy.aerial.wallet import LocalWallet

from uagents.network import get_faucet, get_name_service_contract, _testnet_ledger
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model

from uagents.config import REGISTRATION_FEE


# NOTE: Run agent1.py before running agent2.py


class Message(Model):
    message: str


bob = Agent(
    name="bob-0",
    seed="agent bob-0 secret phrase",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)

fund_agent_if_low(bob)

my_wallet = LocalWallet.from_unsafe_seed("registration test wallet")
name_service_contract = get_name_service_contract()
DOMAIN = "agent"

faucet = get_faucet()
WALLET_BALANCE = _testnet_ledger.query_bank_balance(my_wallet)

if WALLET_BALANCE < REGISTRATION_FEE:
    print("Adding funds to wallet...")
    faucet.get_wealth(my_wallet)
    print("Adding funds to wallet...complete")


@bob.on_event("startup")
async def register_agent_name(ctx: Context):
    await name_service_contract.register(
        bob.ledger, my_wallet, ctx.address[-65:], ctx.name, DOMAIN
    )


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    bob.run()
