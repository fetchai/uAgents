from cosmpy.aerial.wallet import LocalWallet

from uagents.network import get_ledger, get_name_service_contract
from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Model


# NOTE: Run agent1.py before running agent2.py


class Message(Model):
    message: str


bob = Agent(
    name="bob-0",
    seed="agent bob-0 secret phrase",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)

ledger = get_ledger()
my_wallet = LocalWallet.from_unsafe_seed("registration test wallet")
name_service_contract = get_name_service_contract()
domain = "agent"

for wallet in [my_wallet, bob.wallet]:
    fund_agent_if_low(wallet.address())


@bob.on_event("startup")
async def register_agent_name(ctx: Context):
    await name_service_contract.register(
        ledger, my_wallet, ctx.address, ctx.name, domain
    )


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    bob.run()
