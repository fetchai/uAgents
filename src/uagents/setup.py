from uagents.config import REGISTRATION_FEE, get_logger
from uagents.network import get_ledger, get_faucet


LOGGER = get_logger("setup")


def fund_agent_if_low(agent_address: str):
    ledger = get_ledger()
    faucet = get_faucet()

    agent_balance = ledger.query_bank_balance(agent_address)

    if agent_balance < REGISTRATION_FEE:
        # Add tokens to agent's wallet
        LOGGER.info("Adding funds to agent...")
        faucet.get_wealth(agent_address)
        LOGGER.info("Adding funds to agent...complete")
