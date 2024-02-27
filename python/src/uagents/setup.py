"""Agent's Setup."""

import requests
from cosmpy.crypto.address import Address

from uagents import Agent
from uagents.config import REGISTRATION_FEE, get_logger
from uagents.network import get_ledger, get_faucet

LOGGER = get_logger("setup")


def fund_agent_if_low(wallet_address: str, min_balance: int = REGISTRATION_FEE):
    """
    Checks the agent's wallet balance and adds testnet funds if it's below min_balance.

    Args:
        wallet_address (str): The wallet address of the agent.
        min_balance (int): The minimum balance required.

    Returns:
        None
    """
    ledger = get_ledger(test=True)
    faucet = get_faucet()

    agent_balance = ledger.query_bank_balance(Address(wallet_address))

    if agent_balance < min_balance:
        try:
            LOGGER.info("Adding testnet funds to agent...")
            faucet.get_wealth(wallet_address)
            LOGGER.info("Adding testnet funds to agent...complete")
        except Exception as ex:
            LOGGER.error(f"Failed to add testnet funds to agent: {str(ex)}")


def register_agent_with_mailbox(agent: Agent, email: str):
    """
    Registers the agent on a mailbox server using the provided email.

    Args:
        agent (Agent): The agent object to be registered.
        email (str): The email address associated with the agent.

    Returns:
        None
    """
    mailbox = agent.mailbox
    register_url = f"{mailbox['http_prefix']}://{mailbox['base_url']}/v1/auth/register"
    resp = requests.post(
        register_url,
        json={"email": email, "agent_address": agent.address},
        timeout=15,
    )
    if resp.status_code == 200:
        LOGGER.info("Registered agent on mailbox server")
        mailbox["agent_mailbox_key"] = resp.json()["agent_mailbox_key"]
    else:
        LOGGER.exception("Failed to register agent on mailbox server")
