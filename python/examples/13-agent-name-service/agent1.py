from cosmpy.aerial.wallet import LocalWallet

from uagents import Agent, Context, Model
from uagents.network import get_faucet, get_name_service_contract, logger

# NOTE: Run agent1.py before running agent2.py


class Message(Model):
    message: str


DOMAIN = "bob.example.agent"

bob = Agent(
    name="bob",
    domain=DOMAIN,
    seed="agent bob-0 secret phrase",
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)


my_wallet = LocalWallet.from_unsafe_seed("registration test wallet")
name_service_contract = get_name_service_contract(test=True)
faucet = get_faucet()

logger.info(f"Adding testnet funds to {my_wallet.address()}...")
faucet.get_wealth(my_wallet.address())
logger.info(f"Adding testnet funds to {my_wallet.address()}...complete")


@bob.on_interval(10)
async def register_agent_name(ctx: Context):
    await name_service_contract.register(
        bob.ledger, my_wallet, bob.address, bob.name, DOMAIN
    )


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    bob.run()
