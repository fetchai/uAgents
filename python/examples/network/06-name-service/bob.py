from cosmpy.aerial.wallet import LocalWallet
from uagents import Agent, Context, Model
from uagents.network import get_faucet, get_name_service_contract


class Message(Model):
    message: str


BOB_SEED = "put_bobs_seed_phrase_here"

bob = Agent(
    name="bob-0",
    seed=BOB_SEED,
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)


my_wallet = LocalWallet.from_unsafe_seed("registration test wallet")
name_service_contract = get_name_service_contract(test=True)
faucet = get_faucet()
DOMAIN = "example.agent"

faucet.get_wealth(my_wallet.address())


@bob.on_event("startup")
async def register_agent_name(ctx: Context):
    await name_service_contract.register(
        bob.ledger, my_wallet, ctx.address, ctx.name, DOMAIN
    )


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    bob.run()
