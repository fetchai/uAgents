import json
from typing import Optional

from cosmpy.aerial.wallet import LocalWallet

from uagents import Agent, Context, Model
from uagents.network import get_faucet, get_name_service_contract, logger

# NOTE: Run agent1.py before running agent2.py


class VerificationRequest(Model):
    domain: str
    address: str
    chain_id: str


class VerificationResponse(Model):
    domain: str
    info: str
    approval_token: Optional[str]


class Message(Model):
    message: str


bob = Agent(
    name="bob-0",
    seed="agent bob-0 secret phrase",
    port=8001,
    mailbox=True,
)


my_wallet = LocalWallet.from_unsafe_seed("registration test wallet")
name_service_contract = get_name_service_contract()
faucet = get_faucet()
DOMAIN = "agent"

logger.info(f"Adding testnet funds to {my_wallet.address()}...")
faucet.get_wealth(my_wallet.address())
logger.info(f"Adding testnet funds to {my_wallet.address()}...complete")

@bob.on_event("startup")
async def request_token(ctx: Context):
    ctx.logger.info(
        f"Sending verification request to oracle agent for domain {bob.name}.{DOMAIN}"
    )

    oracle_address = name_service_contract.get_oracle_agent_address()

    await ctx.send(
        oracle_address,
        VerificationRequest(
            domain= bob.name + "." + DOMAIN,
            address=str(my_wallet.address()),
            chain_id=ctx.ledger.query_chain_id(),
        ),
    )

    ctx.logger.info("Verification request sent.")


@bob.on_message(model=VerificationResponse)
async def register_agent_name(ctx: Context, sender: str, msg: VerificationResponse):
    if not msg.approval_token:
        ctx.logger.error(f"Domain {msg.domain} is not verified: {msg.info}")
        return

    ctx.logger.info(
        f"Received approval token from {sender} for domain {msg.domain}"
    )
    token = json.loads(msg.approval_token)
    await name_service_contract.register(
        bob.ledger, my_wallet, bob.address, bob.name, DOMAIN, approval_token=token
    )


@bob.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")


if __name__ == "__main__":
    bob.run()
