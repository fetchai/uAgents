import logging

from cosmpy.aerial.client import NetworkConfig
from cosmpy.aerial.faucet import FaucetApi

from nexus.config import REGISTRATION_FEE
from nexus.network import get_ledger


def fund_agent_if_low(agent_address: str):
    ledger = get_ledger("fetchai-testnet")
    faucet_api = FaucetApi(NetworkConfig.latest_stable_testnet())

    agent_balance = ledger.query_bank_balance(agent_address)

    if agent_balance < REGISTRATION_FEE:
        # Add tokens to agent's wallet
        logging.info("Adding funds to agent...")
        faucet_api.get_wealth(agent_address)
        logging.info("Adding funds to agent...complete")
