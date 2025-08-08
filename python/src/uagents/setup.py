"""Agent's Setup."""

from logging import Logger

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.crypto.address import Address

from uagents.config import TESTNET_REGISTRATION_FEE
from uagents.network import get_faucet, get_ledger
from uagents.utils import get_logger

LOGGER: Logger = get_logger("setup")


def fund_agent_if_low(
    wallet_address: str, min_balance: int = TESTNET_REGISTRATION_FEE
) -> None:
    """
    Checks the agent's wallet balance and adds testnet funds if it's below min_balance.

    Args:
        wallet_address (str): The wallet address of the agent.
        min_balance (int): The minimum balance required. Defaults to TESTNET_REGISTRATION_FEE.
    """
    ledger: LedgerClient = get_ledger()
    faucet: FaucetApi = get_faucet()

    agent_balance = ledger.query_bank_balance(Address(wallet_address))

    if agent_balance < min_balance:
        try:
            LOGGER.info("Adding testnet funds to agent...")
            faucet.get_wealth(wallet_address)
            LOGGER.info("Adding testnet funds to agent...complete")
        except Exception as ex:
            LOGGER.error(f"Failed to add testnet funds to agent: {str(ex)}")
