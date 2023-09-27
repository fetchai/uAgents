from cosmpy.aerial.wallet import LocalWallet

from uagents.network import get_ledger, get_faucet, get_name_service_contract
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


my_wallet = LocalWallet.from_unsafe_seed("registration test wallet")
name_service_contract = get_name_service_contract()
DOMAIN = "agent"

faucet = get_faucet()
faucet.get_wealth(my_wallet)

fund_agent_if_low(bob)


@bob.on_event("startup")
async def register_agent_name(ctx: Context):
    await name_service_contract.register(
        bob._ledger, my_wallet, ctx.address, ctx.name, DOMAIN
    )


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    bob.run()
